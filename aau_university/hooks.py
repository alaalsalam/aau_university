app_name = "aau_university"
app_title = "AAU "
app_publisher = "alaalsalam"
app_description = "Custom app for Aljeelalj Adeed University"
app_email = "alaalsalam101@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "aau_university",
# 		"logo": "/assets/aau_university/logo.png",
# 		"title": "AAU ",
# 		"route": "/aau_university",
# 		"has_permission": "aau_university.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/aau_university/css/aau_university.css"
# app_include_js = "/assets/aau_university/js/aau_university.js"

# include js, css files in header of web template
# web_include_css = "/assets/aau_university/css/aau_university.css"
# web_include_js = "/assets/aau_university/js/aau_university.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "aau_university/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "aau_university/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "aau_university.utils.jinja_methods",
# 	"filters": "aau_university.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "aau_university.install.before_install"
# after_install = "aau_university.install.after_install"
# after_migrate = "aau_university.setup.after_migrate.run"
# after_migrate = "aau_university.setup.aau_doctypes_installer.after_migrate"
# Uninstallation
# ------------

# before_uninstall = "aau_university.uninstall.before_uninstall"
# after_uninstall = "aau_university.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "aau_university.utils.before_app_install"
# after_app_install = "aau_university.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "aau_university.utils.before_app_uninstall"
# after_app_uninstall = "aau_university.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "aau_university.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events
doc_events = {
    "Task": {
        "on_update": "aau_university.aau_tasks.task_doctype_importer.on_task_update"
    }
}

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"aau_university.tasks.all"
# 	],
# 	"daily": [
# 		"aau_university.tasks.daily"
# 	],
# 	"hourly": [
# 		"aau_university.tasks.hourly"
# 	],
# 	"weekly": [
# 		"aau_university.tasks.weekly"
# 	],
# 	"monthly": [
# 		"aau_university.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "aau_university.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "aau_university.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "aau_university.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
before_request = ["aau_university.api.v1.routes.ensure_routes"]
after_request = ["aau_university.utils.cors.apply_cors_headers"]

try:
    # WHY+WHAT: eagerly register API URL rules while loading hooks so /api/aau/* paths are available for live HTTP requests without relying on late lazy registration.
    from aau_university.api.v1.routes import ensure_routes as _ensure_aau_api_routes

    _ensure_aau_api_routes()
except Exception:
    # Keep startup resilient; before_request hook still attempts registration per request.
    pass

# Job Events
# ----------
# before_job = ["aau_university.utils.before_job"]
# after_job = ["aau_university.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"aau_university.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
