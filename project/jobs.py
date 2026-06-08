import os
import sys

import requests
import django

curPath = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(curPath)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Kael.settings')
django.setup()

from utils.sync import SyncBaseInfo  # noqa
from users.models import UsersModel  # noqa
from project.models import BusinessesModel, ProductsModel, ApplicationModel  # noqa
from project.constant import app_type_choice, lang_choice, app_level_choice, docker_type_choice  # noqa
from audit.utils import write_audit_log  # noqa


class ProjectSyncData(SyncBaseInfo):

    # Fixed: typos corrected ('phyiscs' -> 'physical', 'virtural' -> 'virtual')
    APP_TYPE_MAP = {
        1: "physical",
        2: "virtual",
    }

    APP_LANG_MAP = {
        1: "java",
        2: "go",
        3: "php",
        4: "python",
        5: "node",
    }

    DOCKER_MAP = {
        0: 'common',
        1: 'docker',
    }

    APP_LEVEL_MAP = {
        1: "s",
        2: "a",
        3: "b",
    }

    def sync_business(self) -> list:
        api = '/api/cmdb/app/v2/business/'
        url = self.generate_url(api)
        total, pages = self.query_records_total(api)
        if not total:
            return []
        records = []
        for page in pages:
            response = requests.get(url, headers=self.headers(), params={'page': page, 'size': self.page_size}, timeout=30)
            try:
                results = response.json()
                records.extend(results.get('results', []))
            except requests.RequestException as err:
                print(f"Error syncing business page {page}: {err}")
        return records

    def sync_product(self) -> list:
        api = '/api/cmdb/app/v2/product/'
        url = self.generate_url(api)
        total, pages = self.query_records_total(api)
        if not total:
            return []
        records = []
        for page in pages:
            response = requests.get(url, headers=self.headers(), params={'page': page, 'size': self.page_size}, timeout=30)
            try:
                results = response.json()
                records.extend(results.get('results', []))
            except requests.RequestException as err:
                print(f"Error syncing product page {page}: {err}")
        return records

    def sync_application(self) -> list:
        api = '/api/cmdb/app/v2/applications/'
        url = self.generate_url(api)
        total, pages = self.query_records_total(api)
        if not total:
            return []
        records = []
        for page in pages:
            response = requests.get(url, headers=self.headers(), params={'page': page, 'size': self.page_size}, timeout=30)
            try:
                results = response.json()
                records.extend(results.get('results', []))
            except requests.RequestException as err:
                print(f"Error syncing application page {page}: {err}")
        return records

    def save_business(self):
        """Sync and save business records. Combined validation + save in one loop."""
        records = self.sync_business()
        saved_count = 0
        error_count = 0
        for item in records:
            try:
                item['instance'] = item['instance_id']
                item['description'] = item.get('description') or ''
                item['create_user'] = item.get('create_user', '')
                del item['instance_id']
                del item['platform_label']

                obj, created = BusinessesModel.objects.update_or_create(
                    instance=item['instance'],
                    defaults={k: item.get(k, '') for k in ['name', 'label', 'platform', 'description', 'create_user']}
                )
                if created:
                    saved_count += 1
            except Exception as err:
                error_count += 1
                print(f"Error saving business {item.get('instance', 'unknown')}: {err}")

        print(f"Business sync complete: {saved_count} created/updated, {error_count} errors")
        # 记录同步审计
        write_audit_log(
            action="sync",
            resource_type="BusinessesModel",
            resource_name="business_sync",
            detail=f"业务线数据同步完成：新增/更新 {saved_count} 条，失败 {error_count} 条",
            operator="system",
        )

    def save_product(self):
        """Sync and save product records. Combined validation + save in one loop."""
        objs_map = {
            i.instance: i
            for i in BusinessesModel.objects.only('instance', 'name')
        }
        records = self.sync_product()
        saved_count = 0
        error_count = 0
        for item in records:
            try:
                item['instance'] = item['instance_id']
                business_obj = objs_map.get(item.get('business_id'))
                del item['instance_id']
                del item['code']
                del item['business_id']

                obj, created = ProductsModel.objects.update_or_create(
                    instance=item['instance'],
                    defaults={
                        'name': item.get('name', ''),
                        'label': item.get('label', ''),
                        'description': item.get('description', ''),
                        'business': business_obj,
                        'create_user': item.get('create_user', ''),
                    }
                )
                if created:
                    saved_count += 1
            except Exception as err:
                error_count += 1
                print(f"Error saving product {item.get('instance', 'unknown')}: {err}")

        print(f"Product sync complete: {saved_count} created/updated, {error_count} errors")
        # 记录同步审计
        write_audit_log(
            action="sync",
            resource_type="ProductsModel",
            resource_name="product_sync",
            detail=f"产品线数据同步完成：新增/更新 {saved_count} 条，失败 {error_count} 条",
            operator="system",
        )

    def save_application(self):
        """Sync and save application records. Combined validation + save in one loop."""
        business_map = {i.instance: i for i in BusinessesModel.objects.only('instance', 'name')}
        user_map = {i.instance: i for i in UsersModel.objects.only('instance')}
        product_map = {i.instance: i for i in ProductsModel.objects.only('instance')}

        records = self.sync_application()
        saved_count = 0
        error_count = 0
        for item in records:
            try:
                item['instance'] = item['instance_id']
                item['business'] = business_map.get(item.get('bussiness_id'))
                item['product'] = product_map.get(item.get('product_id'))
                item['owner'] = user_map.get(item.get('owner'))
                item['lang'] = self.APP_LANG_MAP.get(item.get('lang'), 'java')
                item['level'] = self.APP_LEVEL_MAP.get(item.get('level'), 'b')
                item['mold'] = self.APP_TYPE_MAP.get(item.get('mold'), 'physical')
                item['is_docker'] = self.DOCKER_MAP.get(item.get('is_docker'), 'common')
                item['cost_mode'] = item.get('cost_mode') or 'cpu'
                item['health'] = item.get('health', {})
                item['handle_info'] = item.get('handle_info', '')
                item['create_user'] = item.get('create_user', '')
                item['description'] = item.get('description', '')

                del item['instance_id']
                del item['product_id']
                del item['bussiness_id']
                del item['level_label']
                del item['cost_mode_label']
                del item['mold_label']
                del item['lang_label']
                del item['owner_user']

                defaults = {k: item.get(k) for k in [
                    'name', 'lang', 'level', 'mold', 'cost_mode',
                    'is_docker', 'health', 'handle_info', 'description',
                    'create_user', 'owner', 'business', 'product',
                ]}

                obj, created = ApplicationModel.objects.update_or_create(
                    instance=item['instance'],
                    defaults=defaults
                )
                if created:
                    saved_count += 1
            except Exception as err:
                error_count += 1
                print(f"Error saving application {item.get('instance', 'unknown')}: {err}")

        print(f"Application sync complete: {saved_count} created/updated, {error_count} errors")
        # 记录同步审计
        write_audit_log(
            action="sync",
            resource_type="ApplicationModel",
            resource_name="application_sync",
            detail=f"应用数据同步完成：新增/更新 {saved_count} 条，失败 {error_count} 条",
            operator="system",
        )


if __name__ == '__main__':
    sync = ProjectSyncData()
    sync.save_application()