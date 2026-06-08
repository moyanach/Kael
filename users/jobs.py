import os
import sys

import requests
import django

curPath = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(curPath)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Kael.settings")
django.setup()

from utils.sync import SyncBaseInfo  # noqa
from users.models import UsersModel  # noqa
from audit.utils import write_audit_log  # noqa


class SyncUserInfo(SyncBaseInfo):
    def __init__(self) -> None:
        super(SyncUserInfo, self).__init__()

    def sync_users(self) -> list:
        api = "/api/cmdb/user/v2/user/"
        url = self.generate_url(api)
        total, pages = self.query_records_total(api)
        if not total:
            return []
        records = []
        for page in pages:
            response = requests.get(
                url,
                headers=self.headers(),
                params={"page": page, "size": self.page_size},
                timeout=30,
            )
            try:
                results = response.json()
                records.extend(results.get("results", []))
            except requests.RequestException as err:
                print(f"Error syncing users page {page}: {err}")
        return records

    def save_data(self):
        """Sync and save user records. Combined validation + save in one loop."""
        records = self.sync_users()
        saved_count = 0
        error_count = 0
        for item in records:
            try:
                if "organization_id" not in item:
                    continue

                item["instance"] = item["instance_id"]
                del item["instance_id"]
                del item["organization_id"]

                obj, created = UsersModel.objects.update_or_create(
                    instance=item["instance"],
                    defaults={
                        "username": item.get("username", ""),
                        "nickname": item.get("nickname", ""),
                        "name": item.get("name", ""),
                        "email": item.get("email", ""),
                        "phone": item.get("phone", ""),
                        "sex": item.get("sex", 1),
                        "is_delete": item.get("is_delete", False),
                    }
                )
                if created:
                    saved_count += 1
            except Exception as err:
                error_count += 1
                print(f"Error saving user {item.get('instance', 'unknown')}: {err}")

        print(f"User sync complete: {saved_count} created/updated, {error_count} errors")
        # 记录同步审计
        write_audit_log(
            action="sync",
            resource_type="UsersModel",
            resource_name="user_sync",
            detail=f"用户数据同步完成：新增/更新 {saved_count} 条，失败 {error_count} 条",
            operator="system",
        )


if __name__ == "__main__":
    SyncUserInfo().save_data()