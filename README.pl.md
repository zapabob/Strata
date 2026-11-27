# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

Hakua / Strata to wersja [Niko1221/Strata](https://github.com/Niko1221/Strata) rozwijana z myślą o systemie Windows. Uruchamia lokalne modele do rozmów, programowania i zadań agentowych. W obsługiwanych modelach MoE natywny silnik może rozmieścić wagi ekspertów w pamięci karty graficznej, RAM i na dysku SSD.

## Pierwsze uruchomienie

Pobierz instalator Windows dla bieżącego użytkownika ze [strony wydań Hakua](https://github.com/zapabob/Strata/releases). Silnik CUDA jest udostępniany osobno. W widoku **Modele** wybierz profil zgodny z zainstalowanymi wagami. Inkling 2 Mini SC117 ma osobne profile SQ-10, SQ-15 i SQ-20. Rozmiar kontekstu dobierz do wolnej pamięci. Zobacz [instrukcję Windows](docs/HAKUA_INSTALL.md) i [dokumentację modeli](docs/MODELS.md).

## Ponowne używanie procedur

W **Ustawieniach → Narzędziach** włącz wyszukiwanie umiejętności na żądanie. Agent może odszukać i otworzyć potrzebną instrukcję bez wczytywania całego katalogu. W widoku **Umiejętności** można osobno włączyć uczenie się z ukończonych zadań i automatyczne stosowanie procedur. Procedura to edytowalny plik `SKILL.md`. Automatyczny wybór uwzględnia nazwę, frazę wyzwalającą i obszar roboczy. Umiejętności, pomocnicy, operacje na plikach i `/goal` mają odrębne przełączniki. [Przewodnik po procedurach](docs/WORKFLOW_SKILLS.md)

## Pomiary i ograniczenia

Na RTX 5060 Ti z 16 GB pamięci SC117 SQ-10 utworzył przez `/goal` scenę Pagoda Bench w pojedynczym pliku HTML i poprawił własny kod renderowania po otrzymaniu diagnostyki. Po oddaleniu widoku Chrome pokazał pięć dachów. Scena zgłosiła 7079 wokseli. Początkowy kadr ucinał szczyt, a oficjalnego wyniku jeszcze nie zmierzono. [Pomiary silnika 0.8.5](_docs/2026-11-27_v085-release-notes.md) obejmowały krótkie dane wejściowe przy podanej pojemności kontekstu.

Informacje o zgodności, podpisach i zakresie badań zawiera [rejestr wydań](docs/HAKUA_RELEASE.md). Hakua jest udostępniana na [licencji MIT](LICENSE). Modele i komponenty mają własne warunki.
