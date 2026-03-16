# Vulture whitelist — these are framework-invoked and not dead code.

# FastAPI endpoint functions (called by the framework via @app.get/@app.post decorators)
api_list_images  # noqa
api_get_image  # noqa
api_build_image  # noqa
api_list_containers  # noqa
api_create_container  # noqa
api_start_container  # noqa
api_stop_container  # noqa
api_open_vscode  # noqa
api_delete_container  # noqa
api_version  # noqa
api_prerequisites  # noqa
api_install_gh  # noqa
api_gh_login  # noqa
api_get_settings  # noqa
api_save_settings  # noqa
api_update_check  # noqa
api_update_check_now  # noqa
api_update_download  # noqa
api_shutdown  # noqa
docker_not_available_handler  # noqa
main  # noqa

# FastAPI exception handler requires request parameter in signature
request  # noqa
