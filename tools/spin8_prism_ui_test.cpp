// Link the same generated static UI library as llama-server-impl.
#include "ui.h"
#include <iostream>
int main() {
    const auto & assets=llama_ui_get_assets();
    std::cout << "linked_ui_asset_count=" << assets.size() << '\n';
    return assets.empty() ? 0 : 1;
}
