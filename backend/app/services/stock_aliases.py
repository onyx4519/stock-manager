import unicodedata


# Massive does not provide Korean company names. Keep verified Korean aliases
# separate from provider data so the catalog can be reviewed and expanded.
US_STOCK_KOREAN_ALIASES: dict[str, tuple[str, ...]] = {
    "AAPL": ("애플",),
    "ABNB": ("에어비앤비",),
    "ADBE": ("어도비",),
    "AMD": ("에이엠디",),
    "AMZN": ("아마존",),
    "AVGO": ("브로드컴",),
    "BA": ("보잉",),
    "BRK.B": ("버크셔해서웨이",),
    "CAT": ("캐터필러",),
    "COIN": ("코인베이스",),
    "COST": ("코스트코",),
    "CRM": ("세일즈포스",),
    "CSCO": ("시스코",),
    "CVX": ("셰브론",),
    "DIS": ("디즈니", "월트디즈니"),
    "F": ("포드", "포드모터"),
    "GE": ("제너럴일렉트릭",),
    "GM": ("제너럴모터스",),
    "GOOGL": ("구글", "알파벳"),
    "IBM": ("아이비엠",),
    "INTC": ("인텔",),
    "JNJ": ("존슨앤드존슨",),
    "JOBY": ("조비", "조비에비에이션", "조비항공"),
    "JPM": ("제이피모건", "JP모건"),
    "KO": ("코카콜라",),
    "LCID": ("루시드", "루시드모터스"),
    "LLY": ("일라이릴리",),
    "LMT": ("록히드마틴",),
    "MA": ("마스터카드",),
    "MCD": ("맥도날드",),
    "META": ("메타", "메타플랫폼스"),
    "MRK": ("머크",),
    "MSFT": ("마이크로소프트",),
    "MSTR": ("마이크로스트래티지", "스트래티지"),
    "NFLX": ("넷플릭스",),
    "NKE": ("나이키",),
    "NVDA": ("엔비디아",),
    "ORCL": ("오라클",),
    "PEP": ("펩시", "펩시코"),
    "PFE": ("화이자",),
    "PLTR": ("팔란티어",),
    "QCOM": ("퀄컴",),
    "RIVN": ("리비안",),
    "SBUX": ("스타벅스",),
    "SPOT": ("스포티파이",),
    "TSLA": ("테슬라",),
    "UBER": ("우버",),
    "V": ("비자",),
    "WMT": ("월마트",),
    "XOM": ("엑슨모빌",),
}


def normalize_alias(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


def find_us_tickers_by_korean_alias(
    query: str,
    *,
    limit: int = 20,
) -> tuple[str, ...]:
    term = normalize_alias(query)
    if not term:
        return ()

    matches: list[tuple[int, int, str]] = []
    for ticker, aliases in US_STOCK_KOREAN_ALIASES.items():
        best_rank: tuple[int, int, str] | None = None
        for alias in aliases:
            normalized_alias = normalize_alias(alias)
            if term == normalized_alias:
                rank = (0, len(normalized_alias), ticker)
            elif normalized_alias.startswith(term):
                rank = (1, len(normalized_alias), ticker)
            elif term in normalized_alias:
                rank = (2, len(normalized_alias), ticker)
            else:
                continue
            if best_rank is None or rank < best_rank:
                best_rank = rank
        if best_rank is not None:
            matches.append(best_rank)

    matches.sort()
    return tuple(ticker for _, _, ticker in matches[:limit])
