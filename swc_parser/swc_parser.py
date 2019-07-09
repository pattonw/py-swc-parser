# -*- coding: utf-8 -*-

import numpy as np
import networkx as nx
from pathlib import Path
from typing import Dict, List
from pyparsing import (
    Word,
    Combine,
    Optional,
    OneOrMore,
    ZeroOrMore,
    SkipTo,
    LineEnd,
    Group,
    nums,
    alphas,
)

"""Main module."""

integer = Combine(Optional("-") + Word(nums)).setParseAction(
    lambda s, l, t: [int(t[0])]
)
real = (
    integer ^ Combine(Optional("-") + Word(nums) + "." + Word(nums))
).setParseAction(lambda s, l, t: [float(t[0])])
numeric = real ^ integer

header_line = Group("#" + Word(alphas)("variable") + SkipTo("\n"))

body_line = Group(
    integer("sample_number")
    + integer("structure_identifier")
    + real("x_position")
    + real("y_position")
    + real("z_position")
    + real("radius")
    + integer("parent_sample")
)


def parse_swc(file_path: Path):
    file_string = file_path.open("r").read()
    parsed_rows = (ZeroOrMore(header_line) + ZeroOrMore(body_line)).parseString(
        file_string
    )
    return parsed_rows


def _parse_swc(filename: Path):
    """Read one point per line. If ``ndims`` is 0, all values in one line
    are considered as the location of the point. If positive, only the
    first ``ndims`` are used. If negative, all but the last ``-ndims`` are
    used.
    """
    # initialize file specific variables
    points = []
    header = True
    offset = np.array([0, 0, 0])
    resolution = np.array([1, 1, 1])

    # parse file
    with filename.open() as o_f:
        for line in o_f.read().splitlines():
            if header and line.startswith("#"):
                # Search header comments for variables
                offset = _search_swc_header(line, "offset", offset)
                resolution = _search_swc_header(line, "resolution", resolution)
                continue
            elif line.startswith("#"):
                # comments not in header get skipped
                continue
            elif header:
                # first line without a comment marks end of header
                header = False

            row = line.strip().split()
            if len(row) != 7:
                raise ValueError("SWC has a malformed line: {}".format(line))

            # extract data from row (point_id, type, x, y, z, radius, parent_id)
            points.append(
                {
                    "point_id": int(row[0]),
                    "parent_id": int(row[6]),
                    "point_type": int(row[1]),
                    "location": (np.array([float(x) for x in row[2:5]]) + offset)
                    * resolution,
                    "radius": float(row[5]),
                }
            )
        return _points_to_graph(points)


def _search_swc_header(line: str, key: str, default: np.ndarray) -> np.ndarray:
    # assumes header variables are seperated by spaces
    if key in line.lower():
        print(line.lower().split(key)[1].split())
        value = np.array([float(x) for x in line.lower().split(key)[1].split()])
        return value
    else:
        return default


def _points_to_graph(points: List[Dict]):
    # add points to a temporary graph
    graph = nx.DiGraph()
    for point in points:
        graph.add_node(
            point["point_id"],
            point_type=point["point_type"],
            location=point["location"],
            radius=point["radius"],
        )
        if point["parent_id"] != -1 and point["parent_id"] != point["point_id"]:
            # new connected component
            graph.add_edge(point["parent_id"], point["point_id"])

    # check if the temporary graph is tree like
    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError("SWC skeleton is malformed: it contains a cycle.")

    # assign unique label id's to each connected component
    graph = _relabel_connected_components(graph)

    return graph


def _relabel_connected_components(graph: nx.DiGraph, keep_ids: bool = False):
    # define i in case there are no connected components
    i = -1
    for i, connected_component in enumerate(nx.weakly_connected_components(graph)):
        for node in connected_component:
            graph.nodes[node]["label_id"] = i

    return graph
