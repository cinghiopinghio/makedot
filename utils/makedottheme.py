#!/usr/bin/env python
"""From base colors produce a full palette."""

import argparse
import os
import pathlib

import jinja2
import toml
from colour import Color

HERE = pathlib.Path(__file__).parent


def hex2rgb(hexstr):
    """Convert hex to rgb."""
    hexstr = hexstr.lstrip('#')
    return tuple(int(hexstr[i * 2: i * 2 + 2], 16) / 255 for i in range(3))


def change_lumi(color, sep=0.1):
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
    if isinstance(color1, str):
        color1 = Color(color1)
    if isinstance(color2, str):
        color2 = Color(color2)

    if last:
        return [c.hex_l for c in color1.range_to(color2, steps)]

    return [c.hex_l for c in color1.range_to(color2, steps + 1)][:-1]


def get_env(configuration, path):
    if isinstance(path, str):
        path = pathlib.Path(path)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(path.absolute())),
        autoescape=jinja2.select_autoescape(['html', 'xml'])
    )

    env.filters['darken'] = change_lumi
    env.filters['color_cycle'] = color_cycle
    env.globals.update(zip=zip)
    return env


def get_xdg_data():
    """Return a location to safe compiled files."""
    path = pathlib.Path(
        os.environ.get('XDG_DATA_HOME', pathlib.Path.home() / '.local/share')
    ) / "makedot"
    path.mkdir(parents=True, exist_ok=True)
    return path.absolute()


def prepare_template_path(path):
    """Return where the template should be compiled to."""
    data_path = get_xdg_data()

    if isinstance(path, str):
        path = pathlib.Path(path)

    folder = data_path / 'compiled' / path.parent
    folder.mkdir(parents=True, exist_ok=True)
    return folder / path.stem


def main(configuration, templates):
    """Is main."""

    env = get_env(configuration, templates)
    for template_relpath in env.list_templates():
        print("rendering", template_relpath)
        template = env.get_template(template_relpath)

        # template_relpath = pathlib.Path(template_relpath).s<F12>
        compiled_template = prepare_template_path(template_relpath)
        with open(compiled_template, 'wt') as fout:
            fout.write(template.render(**configuration))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Add some configuration variables to config files.'
    )
    parser.add_argument('dir', type=str, help='path to repo')
    parser.add_argument('-c', '--config', dest='config_path', help='toml file containing the vars')

    args = parser.parse_args()

    if args.config_path is None:
        xdg_config = pathlib.Path(
            os.environ.get(
                "XDG_CONFIG_HOME",
                pathlib.Path.home() / ".config"
            )
        ) / "makedot.toml"

        if not xdg_config.is_file():
            raise FileNotFoundError("Please provide a valid file.")

        filepath = xdg_config
    else:
        filepath = args.config_path

    with open(filepath, 'rt') as fin:
        config = toml.load(fin)

    main(config, args.dir)
