import os
import shutil
import tempfile
from unittest import mock
from unittest.mock import MagicMock

from django.test import TestCase, override_settings
from django.urls import reverse
from file_manager.models import File

from rest_framework import status

MOCK_FILE_RECEIVE_URL = "https://test-url.com/"
VALID_FILES = [("file1.txt", "test-text"), ("file2.txt", "test-text2")]
DUPLICATE_FILES = [("file1.txt", "test-text"), ("file2.txt", "test-text")]


class TransferViewTestCase(TestCase):
    @mock.patch("file_manager.views.transfer.requests.post")
    def _test_success_bulk(
        self, mock_post: MagicMock, files: list, expected_files_num: int
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            expected_url = MOCK_FILE_RECEIVE_URL

            temp_files = []
            for file_name, file_content in files:
                temp_file_path = os.path.join(temp_dir, file_name)
                with open(temp_file_path, "w") as temp_file:
                    temp_file.write(file_content)
                temp_files.append(temp_file_path)

            mock_post.return_value = MagicMock(status_code=status.HTTP_200_OK)

            with override_settings(FILES_FOLDER_PATH=temp_dir):
                response = self.client.post(reverse("transfer"))

            self.assertEqual(mock_post.call_args.args[0], expected_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                len(mock_post.call_args.kwargs["files"]), expected_files_num
            )

    @mock.patch("file_manager.views.transfer.requests.post")
    def _test_success(
        self, mock_post: MagicMock, files: list, expected_files_num: int
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_files = []
            for file_name, file_content in files:
                temp_file_path = os.path.join(temp_dir, file_name)
                with open(temp_file_path, "w") as temp_file:
                    temp_file.write(file_content)
                temp_files.append(temp_file_path)

            mock_post.return_value = MagicMock(status_code=status.HTTP_200_OK)

            with override_settings(FILES_FOLDER_PATH=temp_dir):
                response = self.client.post(reverse("transfer"))

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(mock_post.call_count, expected_files_num)

    @override_settings(FILE_RECEIVE_URL=MOCK_FILE_RECEIVE_URL, SEND_FILES_BULK=True)
    def test_transfer_files_bulk(self):
        files = VALID_FILES

        with self.assertLogs("file_manager.views.transfer") as log_mock:
            self._test_success_bulk(files=files, expected_files_num=2)

        self.assertIn("Files were sent. Response:", log_mock.records[0].getMessage())

        self.assertEqual(File.objects.count(), 2)
        self.assertEqual(File.objects.filter(name="file1.txt").count(), 1)
        self.assertEqual(File.objects.filter(name="file2.txt").count(), 1)

    @override_settings(FILE_RECEIVE_URL=MOCK_FILE_RECEIVE_URL, SEND_FILES_BULK=True)
    def test_duplicate_files_bulk(self):
        files = DUPLICATE_FILES

        with self.assertLogs("file_manager.views.transfer") as log_mock:
            self._test_success_bulk(files=files, expected_files_num=1)

        self.assertIn(
            "File with name file2.txt was already sent once or is a duplicate. Skipping...",
            log_mock.records[0].getMessage(),
        )

        self.assertEqual(File.objects.count(), 1)
        self.assertEqual(File.objects.filter(name="file1.txt").count(), 1)
        self.assertEqual(File.objects.filter(name="file2.txt").count(), 0)

    @mock.patch("file_manager.views.transfer.requests.post")
    @override_settings(FILE_RECEIVE_URL=MOCK_FILE_RECEIVE_URL, SEND_FILES_BULK=True)
    def test_connection_error_bulk(self, mock_post):
        with tempfile.TemporaryDirectory() as temp_dir:
            expected_url = MOCK_FILE_RECEIVE_URL

            temp_files = []
            for file_name, file_content in VALID_FILES:
                temp_file_path = os.path.join(temp_dir, file_name)
                with open(temp_file_path, "w") as temp_file:
                    temp_file.write(file_content)
                temp_files.append(temp_file_path)

            mock_post.side_effect = [ConnectionError()]

            with override_settings(FILES_FOLDER_PATH=temp_dir), self.assertLogs(
                "file_manager.views.transfer",
            ) as log_mock:
                _ = self.client.post(reverse("transfer"))

            self.assertEqual(
                "Files were NOT sent. An Exception has been raised: ",
                log_mock.records[-1].getMessage(),
            )
            self.assertEqual(mock_post.call_args.args[0], expected_url)
            self.assertEqual(File.objects.count(), 0)

    @mock.patch("file_manager.views.transfer.requests.post")
    @override_settings(FILE_RECEIVE_URL=MOCK_FILE_RECEIVE_URL)
    def test_transfer_files(self, mock_post):
        files = VALID_FILES

        with self.assertLogs("file_manager.views.transfer") as log_mock:
            self._test_success(files=files, expected_files_num=2)

        self.assertIn(
            "File file1.txt were sent. Response:", log_mock.records[0].getMessage()
        )
        self.assertIn(
            "File file2.txt were sent. Response:", log_mock.records[-1].getMessage()
        )

        self.assertEqual(File.objects.count(), 2)
        self.assertEqual(File.objects.filter(name="file1.txt").count(), 1)
        self.assertEqual(File.objects.filter(name="file2.txt").count(), 1)

    @override_settings(FILE_RECEIVE_URL=MOCK_FILE_RECEIVE_URL)
    def test_duplicate_files(self):
        files = DUPLICATE_FILES

        with self.assertLogs("file_manager.views.transfer") as log_mock:
            self._test_success(files=files, expected_files_num=1)

        self.assertIn(
            "File file1.txt were sent. Response:", log_mock.records[0].getMessage()
        )
        self.assertIn(
            "File with name file2.txt was already sent once or is a duplicate. Skipping...",
            log_mock.records[-1].getMessage(),
        )

        self.assertEqual(File.objects.count(), 1)
        self.assertEqual(File.objects.filter(name="file1.txt").count(), 1)
        self.assertEqual(File.objects.filter(name="file2.txt").count(), 0)

    @mock.patch("file_manager.views.transfer.requests.post")
    @override_settings(FILE_RECEIVE_URL=MOCK_FILE_RECEIVE_URL)
    def test_connection_error(self, mock_post):
        with tempfile.TemporaryDirectory() as temp_dir:
            expected_url = MOCK_FILE_RECEIVE_URL

            temp_files = []
            for file_name, file_content in VALID_FILES:
                temp_file_path = os.path.join(temp_dir, file_name)
                with open(temp_file_path, "w") as temp_file:
                    temp_file.write(file_content)
                temp_files.append(temp_file_path)

            mock_post.side_effect = [ConnectionError()]

            with override_settings(FILES_FOLDER_PATH=temp_dir), self.assertLogs(
                "file_manager.views.transfer",
            ) as log_mock:
                _ = self.client.post(reverse("transfer"))

        self.assertEqual(
            "Files were NOT sent. An Exception has been raised: ",
            log_mock.records[-1].getMessage(),
        )
        self.assertEqual(mock_post.call_args.args[0], expected_url)
        self.assertEqual(File.objects.count(), 0)

    @mock.patch("file_manager.views.transfer.requests.post")
    @override_settings(FILE_RECEIVE_URL=MOCK_FILE_RECEIVE_URL)
    def test_renamed_file_not_sent_not_created(self, mock_post):
        files = [("file1.txt", "test-text")]
        new_name = "file1_renamed.txt"

        with self.assertLogs("file_manager.views.transfer") as log_mock:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_files = []
                for file_name, file_content in files:
                    temp_file_path = os.path.join(temp_dir, file_name)
                    with open(temp_file_path, "w") as temp_file:
                        temp_file.write(file_content)
                    temp_files.append(temp_file_path)

                mock_post.return_value = MagicMock(status_code=status.HTTP_200_OK)

                with override_settings(FILES_FOLDER_PATH=temp_dir):
                    response = self.client.post(reverse("transfer"))

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(mock_post.call_count, 1)

                self.assertIn(
                    "File file1.txt were sent. Response:",
                    log_mock.records[0].getMessage(),
                )

                self.assertEqual(File.objects.count(), 1)
                self.assertEqual(File.objects.filter(name="file1.txt").count(), 1)

                # Rename the file
                new_file_name = os.path.join(temp_dir, new_name)
                os.rename(temp_files[-1], new_file_name)

                with override_settings(FILES_FOLDER_PATH=temp_dir):
                    response = self.client.post(reverse("transfer"))

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(mock_post.call_count, 1)

                self.assertIn(
                    "File with name file1_renamed.txt was already sent once or is a duplicate. Skipping...",
                    log_mock.records[-1].getMessage(),
                )
                self.assertEqual(File.objects.count(), 1)
                with self.assertRaises(File.DoesNotExist):
                    File.objects.get(name=new_file_name)

    def test_non_existing_folder(self):
        non_exitsting_folder = "this/folder/does/not/exist"
        with self.assertLogs("file_manager.views.transfer") as log_mock:
            with override_settings(FILES_FOLDER_PATH=non_exitsting_folder):
                response = self.client.post(reverse("transfer"))

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertIn(
                    f"The folder `{non_exitsting_folder}` does not exist.",
                    log_mock.records[-1].getMessage(),
                )
                self.assertEqual(File.objects.count(), 0)


class UploadViewTestCase(TestCase):
    def test_upload_file(self):
        file_content = b"Test data"
        url = reverse("transfer-upload")
        non_existing_folder = "./doesnt-exist"

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file_name = os.path.basename(temp_file.name)

        with override_settings(FILES_FOLDER_PATH=non_existing_folder):
            response = self.client.post(url, {"file": open(temp_file.name, "rb")})

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        file_path = os.path.join(non_existing_folder, temp_file_name)
        self.assertTrue(os.path.exists(file_path))

        with open(file_path, "rb") as saved_file:
            saved_content = saved_file.read()
            self.assertEqual(saved_content, file_content)

        shutil.rmtree(non_existing_folder)
