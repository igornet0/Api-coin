LOG_DEFAULT_FORMAT = '[%(asctime)s] %(name)-35s:%(lineno)-3d - %(levelname)-7s - %(message)s'

# Базовая конфигурация для всех окружений
_base_config = {
    "case_sensitive": False,
    "env_file_encoding": "utf-8",
    "env_nested_delimiter": "__",
    "extra": "ignore"
}

# Конфигурация для production
ProdAppBaseConfig = {
    **_base_config,
    "env_file": "./settings/prod.env"
}

# Конфигурация для development  
DevAppBaseConfig = {
    **_base_config,
    "env_file": "./settings/dev.env"
}
    