import asyncio
from datetime import datetime
from typing import Optional

from fastapi import Request
from fastapi.responses import HTMLResponse
from sqladmin import BaseView
# from sqlalchemy import select # Not strictly needed here as CRUD handles selects

from app import crud, models # models might be needed if we access relationships directly in template
from app.database import get_async_db

# Helper to build query string for redirects if ever needed, but form GET does this
# def build_query_string(params: dict) -> str:
# return "&".join(f"{k}={v}" for k, v in params.items() if v is not None and v != "")

class FilteredAttendanceView(BaseView):
    name = "Test View"  # Simplified
    icon = "fas fa-flask" # Changed icon for clarity
    # category = "Attendance Tools" # Temporarily removed

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identity = "testview"  # Simplified, no hyphen

    def is_visible(self, request: Request) -> bool:
        return True

    def is_accessible(self, request: Request) -> bool:
        return True

    async def index(self, request: Request) -> HTMLResponse: # Simplified index
        return HTMLResponse("<h1>Test View Content</h1>")

    # _get_common_head_content can remain if other views might use it,
    # or be removed if this is the only view being tested.
    # For this test, let it remain as it doesn't affect routing.

class AttendanceCSVExportView(BaseView):
    name = "Export Attendance CSV"
    icon = "fas fa-file-csv"
    category = "Attendance Tools"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identity = "export-attendance-csv"

    async def is_visible(self, request: Request) -> bool:
        return True

    async def is_accessible(self, request: Request) -> bool:
        return True

    async def index(self, request: Request) -> HTMLResponse:
        start_date_str = request.query_params.get("start_date", "")
        end_date_str = request.query_params.get("end_date", "")
        event_type = request.query_params.get("event_type", "")
        username = request.query_params.get("username", "")
        user_id = request.query_params.get("user_id", "") # API endpoint supports user_id
        manual_str = request.query_params.get("manual", "")

        content = f"""
        <html>
            <head>
                {FilteredAttendanceView()._get_common_head_content()}
            </head>
            <body>
                <div class="container-fluid mt-3">
                    <h4><i class="{self.icon} mr-1"></i> {self.name}</h4>
                    <p class="text-muted">Configure filters and click "Export CSV" to download the attendance data. The download will use your active API session.</p>
                    <form action="/api/export/csv" method="get" class="mb-3 p-3 border rounded bg-light" target="_blank">
                        <div class="form-row">
                            <div class="form-group col-md-3">
                                <label for="start_date" class="font-weight-bold">Start Date:</label>
                                <input type="datetime-local" id="start_date" name="start_date" value="{start_date_str}" class="form-control form-control-sm">
                            </div>
                            <div class="form-group col-md-3">
                                <label for="end_date" class="font-weight-bold">End Date:</label>
                                <input type="datetime-local" id="end_date" name="end_date" value="{end_date_str}" class="form-control form-control-sm">
                            </div>
                            <div class="form-group col-md-2">
                                <label for="event_type" class="font-weight-bold">Event Type:</label>
                                <select id="event_type" name="event_type" class="form-control form-control-sm">
                                    <option value="" {"selected" if not event_type else ""}>All</option>
                                    <option value="checkin" {"selected" if event_type == "checkin" else ""}>Check In</option>
                                    <option value="checkout" {"selected" if event_type == "checkout" else ""}>Check Out</option>
                                </select>
                            </div>
                            <div class="form-group col-md-2">
                                <label for="username" class="font-weight-bold">Username:</label>
                                <input type="text" id="username" name="username" value="{username}" class="form-control form-control-sm" placeholder="e.g., testuser">
                            </div>
                            <div class="form-group col-md-2">
                                <label for="user_id" class="font-weight-bold">User ID:</label>
                                <input type="number" id="user_id" name="user_id" value="{user_id}" class="form-control form-control-sm" placeholder="e.g., 1">
                            </div>
                        </div>
                        <div class="form-row">
                             <div class="form-group col-md-2">
                                <label for="manual" class="font-weight-bold">Manual Event:</label>
                                <select id="manual" name="manual" class="form-control form-control-sm">
                                   <option value="" {"selected" if manual_str == "" else ""}>All</option>
                                    <option value="true" {"selected" if manual_str == "true" else ""}>Yes</option>
                                    <option value="false" {"selected" if manual_str == "false" else ""}>No</option>
                                </select>
                            </div>
                            <div class="form-group col-md-3 d-flex align-items-end">
                                <button type="submit" class="btn btn-success btn-sm btn-block"><i class="fas fa-download mr-1"></i> Export CSV</button>
                            </div>
                        </div>
                    </form>
                    <p><small>Note: The CSV will be generated based on the filters applied. The download should start automatically. If not, check your browser's pop-up blocker.</small></p>
                </div>
            </body>
        </html>
        """
        return HTMLResponse(content=content)

class AdminAttendanceReportView(BaseView):
    name = "Admin Attendance Report"
    icon = "fas fa-chart-line"
    category = "Attendance Tools"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identity = "admin-attendance-report"

    async def is_visible(self, request: Request) -> bool:
        # This view should ideally only be visible to admin users
        # Example: Check a session variable set during SQLAdmin login
        # if hasattr(request.state, 'user') and request.state.user.is_admin:
        # return True
        return True # For now, visible to all; implement proper auth check

    async def is_accessible(self, request: Request) -> bool:
        return True # Implement proper auth check

    async def index(self, request: Request) -> HTMLResponse:
        start_date_str = request.query_params.get("start_date", "")
        end_date_str = request.query_params.get("end_date", "")
        include_details_str = request.query_params.get("include_details", "true")

        content = f"""
        <html>
            <head>
                {FilteredAttendanceView()._get_common_head_content()}
            </head>
            <body>
                <div class="container-fluid mt-3">
                    <h4><i class="{self.icon} mr-1"></i> {self.name}</h4>
                    <p class="text-muted">Select date range and options to generate the attendance report as a CSV file.</p>
                    <form action="/api/admin/report" method="get" class="mb-3 p-3 border rounded bg-light" target="_blank">
                        <div class="form-row">
                            <div class="form-group col-md-4">
                                <label for="start_date" class="font-weight-bold">Start Date (Required):</label>
                                <input type="datetime-local" id="start_date" name="start_date" value="{start_date_str}" class="form-control form-control-sm" required>
                            </div>
                            <div class="form-group col-md-4">
                                <label for="end_date" class="font-weight-bold">End Date (Required):</label>
                                <input type="datetime-local" id="end_date" name="end_date" value="{end_date_str}" class="form-control form-control-sm" required>
                            </div>
                            <div class="form-group col-md-2">
                                <label for="include_details" class="font-weight-bold">Include Details:</label>
                                <select id="include_details" name="include_details" class="form-control form-control-sm">
                                    <option value="true" {"selected" if include_details_str == "true" else ""}>Yes</option>
                                    <option value="false" {"selected" if include_details_str == "false" else ""}>No</option>
                                </select>
                            </div>
                            <div class="form-group col-md-2 d-flex align-items-end">
                                <button type="submit" class="btn btn-info btn-sm btn-block"><i class="fas fa-file-alt mr-1"></i> Generate Report</button>
                            </div>
                        </div>
                    </form>
                     <p><small>Note: The report will be generated as a CSV file. The download should start automatically. Ensure start and end dates are provided.</small></p>
                </div>
            </body>
        </html>
        """
        return HTMLResponse(content=content) 