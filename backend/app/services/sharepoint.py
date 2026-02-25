from dataclasses import dataclass


@dataclass
class SharePointUploadResult:
    status: str
    destination_path: str
    files_uploaded: int


class MockSharePointUploader:
    """SharePoint uploader stub.

    TODO: Replace with Microsoft Graph API implementation using env credentials.
    """

    def upload_record(self, destination_path: str, files_uploaded: int) -> SharePointUploadResult:
        return SharePointUploadResult(
            status="success",
            destination_path=destination_path,
            files_uploaded=files_uploaded,
        )
