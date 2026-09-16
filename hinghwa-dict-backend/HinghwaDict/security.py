UNSAFE_DEVELOPMENT_SECRET_KEY = "unsafe-development-only-do-not-use-in-production"


def load_secret_key(env, debug):
    """Load Django's secret, allowing a known-unsafe fallback only in debug."""
    if debug:
        return env.str("SECRET_KEY", default=UNSAFE_DEVELOPMENT_SECRET_KEY)
    return env.str("SECRET_KEY")
