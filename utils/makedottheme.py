#!/usr/bin/env python
"""From base colors produce a full palette."""

import argparse
import os
import pathlib

import colour
import jinja2
import toml

HERE = pathlib.Path(__file__).parent


class Color(colour.Color):
    """A Class for colors."""

    @property
    def d(self):
        """Darken this color."""
        return change_lumi(self, sep=0.1)

    @property
    def l(self):
        """Lighten this color."""
        return change_lumi(self, sep=-0.1)

    def __repr__(self):
        return self.hex_l

    def __str__(self):
        return self.hex_l


def hex2rgb(hexstr):
    """Convert hex to rgb."""
    hexstr = hexstr.lstrip("#")
    return tuple(int(hexstr[i * 2 : i * 2 + 2], 16) / 255 for i in range(3))


def change_lumi(color, sep=0.1):
    """Increase or decrease the luminance.

    Parameters
    ----------
    color : Color or str
        a color as Color class or hex string.
    sep : float
        amount of change within the interval [0: 1]

    Return
    ------
    color : Color
        a new color with new luminance.
    """
    _color = Color(color)

    lumi = _color.get_luminance() - sep
    lumi = max(0, min(1, lumi))
    _color.set_luminance(lumi)
    return _color


def rgb2xterm(rgb):
    """Convert rgb to 16bits."""
    N = []
    for i, n in enumerate([47, 68, 40, 40, 40, 21]):
        N.extend([i] * n)
    _rgb = [int(c * 255 + 0.5) for c in rgb]
    cmax = max(*_rgb)
    cmin = min(*_rgb)

    if (cmax - cmin) * (cmax + cmin) <= 6250:
        cgray = 24 - (252 - (sum(_rgb) // 3)) // 10
        # print(cgray)
        if 0 <= cgray <= 25:
            return 232 + min(cgray, 23)

    return 16 + 36 * N[_rgb[0]] + 6 * N[_rgb[1]] + N[_rgb[2]]


def color_cycle(color1, color2, steps, last=False):
    """Return a list of colors between the two given colors."""
    if isinstance(color1, str):
        color1 = Color(color1)
    if isinstance(color2, str):
        color2 = Color(color2)

    if last:
        return [c.hex_l for c in color1.range_to(color2, steps)]

    return [c.hex_l for c in color1.range_to(color2, steps + 1)][:-1]


def get_env(configuration, path):
    """Get environment and set jinja2 environment."""
    if isinstance(path, str):
        path = pathlib.Path(path)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(path.absolute())),
        autoescape=jinja2.select_autoescape(["html", "xml"]),
    )

    env.filters["darken"] = change_lumi
    env.filters["color_cycle"] = color_cycle
    env.filters["lstrip"] = lambda x, y: str(x).lstrip(y)
    env.filters["rstrip"] = lambda x, y: str(x).rstrip(y)
    env.globals.update(zip=zip)
    env.globals.update(cycle=color_cycle)
    return env


def get_xdg_data():
    """Return a location to safe compiled files."""
    path = (
        pathlib.Path(
            os.environ.get("XDG_DATA_HOME", pathlib.Path.home() / ".local/share")
        )
        / "makedot"
    )
    path.mkdir(parents=True, exist_ok=True)
    return path.absolute()


def prepare_template_path(path):
    """Return where the template should be compiled to."""
    data_path = get_xdg_data()

    if isinstance(path, str):
        path = pathlib.Path(path)

    folder = data_path / "compiled" / path.parent
    folder.mkdir(parents=True, exist_ok=True)
    return folder / path.stem


def get_config(config_path):
    """Read configuration with defaluts."""
    with open(config_path, "rt") as fin:
        config = toml.load(fin)

    default_base = {
        "white": "#ffffff",
        "black": "#000000",
        "light": "#eeeeee",
        "dark": "#111111",
    }
    default_base.update(config.get("base", {}))
    default_base = {k: Color(v) for k, v in default_base.items()}

    default_colors = {
        "red": "#aa0000",
        "green": "#00aa00",
        "yellow": "#aaaa00",
        "blue": "#0000aa",
        "magenta": "#aa00aa",
        "cyan": "#00aaaa",
    }
    config.setdefault("xterm_names", list(default_colors.keys()))

    default_colors.update(config.get("colors", {}))
    default_colors = {k: Color(v) for k, v in default_colors.items()}

    config["colors"] = default_colors
    config["base"] = default_base

    if "xterm_dark" not in config:
        xterm = {
            "0": default_base["black"],
            "8": default_base["dark"].l.l,
            "7": default_base["light"].d.d,
            "15": default_base["white"],
        }
        for ix, xname in enumerate(config["xterm_names"]):
            xterm[str(ix + 1)] = default_colors[xname]
            xterm[str(ix + 9)] = default_colors.get(
                xname + "_light", default_colors[xname].l.l
            )

        config["xterm_dark"] = xterm

    if "xterm_light" not in config:
        xterm = {
            "0": default_base["white"],
            "8": default_base["light"].d.d,
            "7": default_base["dark"].l.l,
            "15": default_base["black"],
        }
        for ix, xname in enumerate(config["xterm_names"]):
            xterm[str(ix + 1)] = default_colors[xname]
            xterm[str(ix + 9)] = default_colors.get(
                xname + "_light", default_colors[xname].d.d
            )

        config["xterm_light"] = xterm

    return config


def main(configuration_path, templates):
    """Is main."""
    configuration = get_config(configuration_path)

    env = get_env(configuration, templates)
    for template_relpath in env.list_templates():
        print("rendering", template_relpath)
        template = env.get_template(template_relpath)

        # template_relpath = pathlib.Path(template_relpath).s<F12>
        compiled_template = prepare_template_path(template_relpath)
        with open(compiled_template, "wt") as fout:
            fout.write(template.render(**configuration))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add some configuration variables to config files."
    )
    parser.add_argument("dir", type=str, help="path to repo")
    parser.add_argument(
        "-c", "--config", dest="config_path", help="toml file containing the vars"
    )

    args = parser.parse_args()

    if args.config_path is None:
        xdg_config = (
            pathlib.Path(
                os.environ.get("XDG_CONFIG_HOME", pathlib.Path.home() / ".config")
            )
            / "makedot.toml"
        )

        if not xdg_config.is_file():
            raise FileNotFoundError("Please provide a valid file.")

        config_path = xdg_config
    else:
        config_path = args.config_path

    main(config_path, args.dir)
