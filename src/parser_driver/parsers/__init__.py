__all__ = ("ParserNews", "ParserKucoin", "KuCoinAPI",
            "ParserNewsApi", "TelegramParser")

from src.core.utils.gui_deps import GUICheck

if GUICheck.has_gui_deps():
    from .parser_news import ParserNews
    from .parser_kucoin import ParserKucoin
else:
    class ParserKucoin: pass
    class ParserNews: pass

from .parser_kucoin_api import KuCoinAPI
from .parser_news_api import ParserNewsApi
from .parser_telegram import TelegramParser