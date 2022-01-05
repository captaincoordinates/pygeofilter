# ------------------------------------------------------------------------------
#
# Project: pygeofilter <https://github.com/geopython/pygeofilter>
# Authors: Fabian Schindler <fabian.schindler@eox.at>, David Bitner <bitner@dbspatial.com>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2021 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------

from typing import Dict

import shapely.geometry

from ..evaluator import Evaluator, handle
from ... import ast
from ... import values

from ...parsers.cql2_json import parser

COMPARISON_OP_MAP = {v: k for k, v in parser.COMPARISON_MAP.items()}
ARITHMETIC_OP_MAP = {v: k for k, v in parser.ARITHMETIC_MAP.items()}
SPATIAL_COMPARISON_OP_MAP = {
    v: k for k, v in parser.SPATIAL_PREDICATES_MAP.items()
}
TEMPORAL_COMPARISON_OP_MAP = {
    v: k for k, v in parser.TEMPORAL_PREDICATES_MAP.items()
}
ARRAY_COMPARISON_OP_MAP = {
    v: k for k, v in parser.ARRAY_PREDICATES_MAP.items()
}


def baseop(map, node, *args):
    if map is None:
        return {"op": node.op.value, "args": [*args]}
    else:
        for k, v in map.items():
            if isinstance(node, v):
                return {"op": k, "args": [*args]}
    raise Exception("No op found")


class CQL2Evaluator(Evaluator):
    def __init__(
        self, attribute_map: Dict[str, str], function_map: Dict[str, str]
    ):
        self.attribute_map = attribute_map
        self.function_map = function_map

    @handle(ast.Not, ast.And, ast.Or)
    def nomap(self, node, *args):
        return baseop(None, node, *args)

    @handle(ast.Comparison, subclasses=True)
    def comparison(self, node, *args):
        return baseop(parser.COMPARISON_MAP, node, *args)

    @handle(ast.TemporalPredicate, subclasses=True)
    def temporal(self, node, *args):
        return baseop(parser.TEMPORAL_PREDICATES_MAP, node, *args)

    @handle(ast.SpatialComparisonPredicate, subclasses=True)
    def spatial(self, node, *args):
        return baseop(parser.SPATIAL_PREDICATES_MAP, node, *args)

    @handle(ast.ArithmeticOp, subclasses=True)
    def spatial(self, node, *args):
        return baseop(parser.ARRAY_PREDICATES_MAP, node, *args)

    @handle(ast.ArrayComparisonOp, subclasses=True)
    def spatial(self, node, *args):
        return baseop(parser.ARRAY_PREDICATES_MAP, node, *args)

    # @handle(ast.Between)
    # def between(self, node, lhs, low, high):
    #     return {"between": ["value": lhs, "lower": low, "upper": high]}
    #     return f"({lhs} {'NOT ' if node.not_ else ''}BETWEEN {low} AND {high})"

    # @handle(ast.Like)
    # def like(self, node, lhs):
    #     pattern = node.pattern
    #     if node.wildcard != "%":
    #         # TODO: not preceded by escapechar
    #         pattern = pattern.replace(node.wildcard, "%")
    #     if node.singlechar != "_":
    #         # TODO: not preceded by escapechar
    #         pattern = pattern.replace(node.singlechar, "_")

    #     # TODO: handle node.nocase
    #     return {"like": [lhs, pattern]}
    #     return f"{lhs} {'NOT ' if node.not_ else ''}LIKE '{pattern}' ESCAPE '{node.escapechar}'"

    # @handle(ast.In)
    # def in_(self, node, lhs, *options):
    #     return {"in": {"value": lhs, "list": options}}

    @handle(ast.IsNull)
    def null(self, node, lhs):
        return {"op":"isNull", "args": lhs}


    # @handle(ast.BBox)
    # def bbox(self, node, lhs):
    #     func = SPATIAL_COMPARISON_OP_MAP[ast.SpatialComparisonOp.INTERSECTS]
    #     # TODO: create BBox geometry
    #     return {func: [lhs, rhs]}

    @handle(ast.Attribute)
    def attribute(self, node: ast.Attribute):
        return {"property": node.name}


    @handle(*values.LITERALS)
    def literal(self, node):
        return node

    @handle(values.Geometry)
    def geometry(self, node: values.Geometry):
        return shapely.geometry.shape(node).__geo_interface__

    @handle(values.Envelope)
    def envelope(self, node: values.Envelope):
        return shapely.geometry.box(
            node.x1, node.y1, node.x2, node.y2
        ).__geo_interface__


def to_cql2(
    root: ast.Node,
    field_mapping: Dict[str, str] = None,
    function_map: Dict[str, str] = None,
) -> str:
    return CQL2Evaluator(field_mapping, function_map).evaluate(root)
