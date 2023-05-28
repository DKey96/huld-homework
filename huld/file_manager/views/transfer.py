import logging
import os
import time
from hashlib import md5
from pathlib import Path

import requests
from django.conf import settings
from django.db.models import Q
from file_manager.models import File
from file_manager.serializers.upload import UploadSerializer

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response

log = logging.getLogger(__name__)


class TransferView(viewsets.GenericViewSet):
    """View for handling the transfer of the files to the external service via HTTPS"""

    def create(self, request, *args, **kwargs) -> Response:
        if settings.SEND_FILES_BULK:
            response = self._send_files_bulk()
        else:
            response = self._send_files_by_one()
        return response

    @staticmethod
    def _get_files(folder_path: str) -> list[str]:
        try:
            return sorted(os.listdir(folder_path))
        except FileNotFoundError:
            log.error("The folder `%s` does not exist.", folder_path)
            return []

    def _send_files_by_one(self) -> Response:
        """
        Send files to the external URL one-by-one.
        Thus, this method results in multiple requests to the external endpoint.
        """
        folder_path = settings.FILES_FOLDER_PATH
        files = self._get_files(folder_path)

        for file_name in files:
            file_path = os.path.join(folder_path, file_name)

            if os.path.isfile(file_path):
                with open(file_path, "rb") as file:
                    files_md5 = md5(file.read()).hexdigest()
                    files_number = os.stat(file_path, follow_symlinks=False).st_ino

                    try:
                        _ = File.objects.get(
                            Q(md5_hash=files_md5) | Q(file_number=files_number)
                        )
                    except File.DoesNotExist:
                        try:
                            response = requests.post(
                                settings.FILE_RECEIVE_URL,
                                files={"file": (file_name, file)},
                            )

                            if response.status_code >= 400:
                                log.error(
                                    "File %s was NOT sent. There was an error with the external service. Response: ",
                                    file_name,
                                    response.text,
                                )
                                return Response(
                                    status=status.HTTP_424_FAILED_DEPENDENCY
                                )

                            _ = File.objects.create(
                                name=file_name,
                                md5_hash=files_md5,
                                path=file.name,
                                file_number=files_number,
                            )
                            log.info(
                                "File %s were sent. Response: Status-code: %s, Text: %s",
                                file_name,
                                response.status_code,
                                response.text,
                            )
                            # Sleep so we don't overwhelm the external endpoint
                            time.sleep(1)
                        except ConnectionError as e:
                            log.error(
                                "Files were NOT sent. An Exception has been raised: %s",
                                str(e),
                            )
                            return Response(status=status.HTTP_424_FAILED_DEPENDENCY)
                    else:
                        log.info(
                            "File with name %s was already sent once or is a duplicate. Skipping...",
                            file_name,
                        )
        return Response(status=status.HTTP_200_OK)

    def _send_files_bulk(self) -> Response:
        """
        Send files to the external URL as a bulk.
        Thus, all the files are sent to the external URL as one request.
        """
        folder_path = settings.FILES_FOLDER_PATH
        files = self._get_files(folder_path)

        files_to_be_sent = []
        created_files = []
        for file_name in files:
            file_path = os.path.join(folder_path, file_name)

            if os.path.isfile(file_path):
                with open(file_path, "rb") as file:
                    files_md5 = md5(file.read()).hexdigest()
                    files_number = os.stat(file_path, follow_symlinks=False).st_ino
                    try:
                        _ = File.objects.get(
                            Q(md5_hash=files_md5) | Q(file_number=files_number)
                        )
                    except File.DoesNotExist:
                        file_model = File.objects.create(
                            name=file_name,
                            md5_hash=files_md5,
                            path=file.name,
                            file_number=files_number,
                        )
                        files_to_be_sent.append(("files", (file_name, file)))
                        created_files.append(file_model)
                    else:
                        log.info(
                            "File with name %s was already sent once or is a duplicate. Skipping...",
                            file_name,
                        )
        if files_to_be_sent:
            try:
                response = requests.post(
                    settings.FILE_RECEIVE_URL, files=files_to_be_sent
                )
                if response.status_code >= 400:
                    log.error(
                        "Files were NOT sent. There was an error with the external service. Response: ",
                        response.text,
                    )
                    # Files must be deleted from the DB, as the request failed, so we can send them again
                    for file in created_files:
                        file.delete()
                    return Response(status=status.HTTP_424_FAILED_DEPENDENCY)
                log.info(
                    "Files were sent. Response: Status-code: %s, Text: %s",
                    response.status_code,
                    response.text,
                )
            except ConnectionError as e:
                log.error(
                    "Files were NOT sent. An Exception has been raised: %s", str(e)
                )
                # Files must be deleted from the DB, as the request failed, so we can send them again
                for file in created_files:
                    file.delete()

                return Response(status=status.HTTP_424_FAILED_DEPENDENCY)
        return Response(status=status.HTTP_200_OK)

    @action(
        methods=["post"],
        detail=False,
        name="upload",
        parser_class=FileUploadParser,
    )
    def upload(self, request, *args, **kwargs) -> Response:
        """Enables user to upload a file over the API. Meant to be used for testing of the functionality"""
        file = request.FILES.get("file")

        serializer = UploadSerializer(data={"file": file})
        serializer.is_valid(raise_exception=True)
        validated_file = serializer.validated_data.get("file")
        filename = validated_file.name

        file_path = os.path.join(settings.FILES_FOLDER_PATH, filename)
        if not os.path.exists(settings.FILES_FOLDER_PATH):
            path = Path(settings.FILES_FOLDER_PATH)
            path.mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb+") as destination:
            for chunk in validated_file.chunks():
                print(chunk)
                destination.write(chunk)
        return Response(status=204)
