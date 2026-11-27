from statistics import median

from checkedtables.words import Page, Word


def step_2_rule_lines(page: Page) -> tuple[tuple[Word, ...], ...]:
    if not page.words:
        return ()
    tolerance = 0.35 * median(word.box.bottom - word.box.top for word in page.words)
    lines: list[list[Word]] = []
    for word in sorted(page.words, key=lambda word: (word.box.bottom, word.box.x0, word.ref)):
        if lines and word.box.bottom - lines[-1][0].box.bottom <= tolerance:
            lines[-1].append(word)
        else:
            lines.append([word])
    return tuple(tuple(line) for line in lines)
