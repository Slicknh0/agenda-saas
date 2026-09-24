from pydantic_settings import BaseSettings, SettingsConfigDict

# Segredos de exemplo que NUNCA podem chegar em produção. O primeiro é o
# antigo default versionado no código — como o repositório é público, ele é
# de conhecimento geral e permitiria forjar tokens de qualquer tenant.
INSECURE_JWT_SECRETS = frozenset(
    {
        "",
        "dev-secret-change-in-production",
        "troque-isso-em-producao",
    }
)
MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # debug=True libera os defaults de conveniência para rodar localmente.
    # Em produção defina DEBUG=false; aí o segredo JWT é validado no boot.
    debug: bool = False

    database_url: str = "sqlite:///./agenda.db"
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    free_plan_max_services: int = 3

    rate_limit_enabled: bool = True

    def model_post_init(self, __context: object) -> None:
        if self.debug:
            return
        if self.jwt_secret in INSECURE_JWT_SECRETS:
            raise RuntimeError(
                "JWT_SECRET nao configurado: defina um segredo forte via ambiente "
                "antes de rodar em producao (ou use DEBUG=true em desenvolvimento)."
            )
        if len(self.jwt_secret) < MIN_JWT_SECRET_LENGTH:
            raise RuntimeError(
                f"JWT_SECRET fraco: use no minimo {MIN_JWT_SECRET_LENGTH} caracteres."
            )


settings = Settings()
