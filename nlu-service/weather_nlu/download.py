from weather_nlu.encoder import MINILM_MODEL
from weather_nlu.models import download_model


def main() -> None:
    download_model(MINILM_MODEL)


if __name__ == "__main__":
    main()
