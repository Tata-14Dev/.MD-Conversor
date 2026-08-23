import os
import sys

try:
    import msvcrt
except ImportError:
    msvcrt = None

try:
    import readline
except ImportError:
    readline = None


def _split(text: str) -> tuple[str, str]:
    idx = max(text.rfind("\\"), text.rfind("/"))
    if idx == -1:
        return "", text
    return text[: idx + 1], text[idx + 1 :]


def _complete(text: str) -> tuple[str, list[str]]:
    quote = text[:1] if text[:1] in ("'", '"') else ""
    body = text[len(quote):]

    base_dir, prefix = _split(body)
    lookup_dir = os.path.expandvars(base_dir) if base_dir else "."
    try:
        entries = os.listdir(lookup_dir)
    except OSError:
        return text, []

    prefix_lower = prefix.lower()
    matches = sorted(e for e in entries if e.lower().startswith(prefix_lower))
    if not matches:
        return text, []

    if len(matches) == 1:
        name = matches[0]
        suffix = os.sep if os.path.isdir(os.path.join(lookup_dir, name)) else ""
        return f"{quote}{base_dir}{name}{suffix}", []

    common = os.path.commonprefix(matches)
    if common and common.lower() != prefix.lower():
        return f"{quote}{base_dir}{common}", matches
    return text, matches


def _read_path_with_completion(prompt: str) -> str:
    sys.stdout.write(prompt)
    sys.stdout.flush()
    buf = ""
    last_matches: list[str] = []

    while True:
        ch = msvcrt.getwch()

        if ch in ("\r", "\n"):
            sys.stdout.write("\n")
            return buf

        if ch == "\x03":
            raise KeyboardInterrupt

        if ch == "\x08":
            if buf:
                buf = buf[:-1]
                sys.stdout.write("\b \b")
                sys.stdout.flush()
            last_matches = []
            continue

        if ch in ("\x00", "\xe0"):
            msvcrt.getwch()
            continue

        if ch == "\t":
            new_buf, matches = _complete(buf)
            if matches and matches == last_matches:
                sys.stdout.write("\n" + "  ".join(matches) + "\n" + prompt + buf)
                sys.stdout.flush()
            elif new_buf != buf:
                sys.stdout.write(new_buf[len(buf):])
                sys.stdout.flush()
                buf = new_buf
            last_matches = matches
            continue

        buf += ch
        sys.stdout.write(ch)
        sys.stdout.flush()
        last_matches = []


def _readline_completer(text: str, state: int) -> str | None:
    quote = text[:1] if text[:1] in ("'", '"') else ""
    body = text[len(quote):]

    base_dir, prefix = _split(body)
    lookup_dir = os.path.expandvars(base_dir) if base_dir else "."
    try:
        entries = os.listdir(lookup_dir)
    except OSError:
        entries = []

    prefix_lower = prefix.lower()
    names = sorted(e for e in entries if e.lower().startswith(prefix_lower))
    candidates = []
    for name in names:
        full = f"{quote}{base_dir}{name}"
        if os.path.isdir(os.path.join(lookup_dir, name)):
            full += os.sep
        candidates.append(full)

    if state < len(candidates):
        return candidates[state]
    return None


def _read_path_with_readline(prompt: str) -> str:
    old_completer = readline.get_completer()
    old_delims = readline.get_completer_delims()
    readline.set_completer(_readline_completer)
    readline.set_completer_delims("\t\n")
    if "libedit" in (readline.__doc__ or ""):
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")
    try:
        return input(prompt)
    finally:
        readline.set_completer(old_completer)
        readline.set_completer_delims(old_delims)


def prompt_path(prompt: str) -> str:
    if not sys.stdin.isatty():
        return input(prompt)
    if msvcrt is not None:
        return _read_path_with_completion(prompt)
    if readline is not None:
        return _read_path_with_readline(prompt)
    return input(prompt)
