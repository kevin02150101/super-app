class MyCamError(Exception):
    """Unified application exception — caught by API / controller layers and returned as JSON or rendered as a page."""

    def __init__(self, code: str, message: str, http_status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status

    def to_dict(self):
        return {"code": self.code, "message": self.message}
