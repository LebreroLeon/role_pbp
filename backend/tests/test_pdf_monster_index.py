from app.rules.dnd5e.pdf_monster_index import (
    MonsterIndexEntry,
    parse_text_index_pages,
    resolve_index_entry,
    scan_stat_blocks_in_pages,
)


class TestPdfMonsterIndex:
    def test_parse_text_index_dots(self):
        pages = {
            1: "ÍNDICE\nGoblin ........................ 178\nDragón Rojo .............. 98\n",
        }
        entries = parse_text_index_pages(pages)
        assert len(entries) == 2
        assert entries[0].name == "Goblin"
        assert entries[0].page == 178
        assert entries[0].source == "text_index"

    def test_scan_stat_blocks_on_page(self):
        pages = {
            178: "GOBLIN\nHumanoide Pequeño (trasgo), neutral malvado\nClase de Armadura: 15\n",
        }
        entries = scan_stat_blocks_in_pages(pages)
        assert len(entries) == 1
        assert entries[0].name == "Goblin"
        assert entries[0].page == 178

    def test_resolve_index_entry_partial(self):
        index = [
            MonsterIndexEntry(name="Neothelido", page=177, source="text_index"),
            MonsterIndexEntry(name="Goblin", page=178, source="text_index"),
        ]
        assert resolve_index_entry(index, "neothelido") is not None
        assert resolve_index_entry(index, "neothelido").page == 177
