#!/usr/bin/env python3
"""CoD2 Menu Builder — entry point."""

from menu_builder.gui.app import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
