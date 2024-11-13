import asyncio

from unitelabs.cdk import Connector

from sila2_feature_lib.reportgen.v001_0.feature_ul import ReportGenController


async def main():
    # Create a new server
    app = Connector(
        {
            "sila_server": {
                "name": "Report Generator Server",
                "type": "ReportGenServer",
                "description": "Server for report generation",
                "version": "1.0.0",
                "vendor_url": "https://www.novonordisk.com/",
            }
        }
    )

    # Let's define a report generator function
    class MyReportGen(ReportGenController):
        async def generate_report(self, identifier: str, additional_info: str) -> str:
            return f"TEST_ID_0001"  # Do nothing and return an "ID"

    # Register the feature to the server
    app.register(MyReportGen())

    # Backwards compatibility fix - our scheduler won't run version 1.1 :-(
    [setattr(f, "sila2_version", "1.0") for f in app.sila_server.features.values()]

    await app.start()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
