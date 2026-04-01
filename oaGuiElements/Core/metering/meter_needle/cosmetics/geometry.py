# cosmetics/geometry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import math
from dataclasses import dataclass
from typing import List, Tuple

try:
    from oaneedlegeometry_rs import NeedleGeometry
    needle_geo_rs = NeedleGeometry()
except ImportError:
    needle_geo_rs = None

from oaGuiElements.Core.metering.meter_needle.constants import (
    SAFE_MARGIN, SHAPE_MULTIPLIERS, SHAPE_Y_SHIFTS,
    SQUIRCLE_N, SQUIRCLE_WIDTH_FACTOR, SQUIRCLE_HEIGHT_FACTOR, 
    SQUECTANGLE_WIDTH_FACTOR, SQUECTANGLE_HEIGHT_FACTOR,
    SQUIRCLE_STEPS,
    CREST_CURVE_STEPS, CREST_TOP_WIDTH_FACTOR, CREST_TOP_HEIGHT_FACTOR, CREST_BOTTOM_HEIGHT_FACTOR,
    HOTDOG_WIDTH_STRAIGHT, HOTDOG_HEIGHT_TOTAL, HOTDOG_CAP_RADIUS, HOTDOG_CAP_CENTER_Y,
    CYLINDER_WIDTH_STRAIGHT, CYLINDER_HEIGHT_TOTAL, CYLINDER_CAP_RADIUS, CYLINDER_CAP_CENTER_Y, CYLINDER_STEPS,
    GEM_WIDTH_FACTOR, GEM_BASE_HEIGHT, GEM_SHOULDER_WIDTH, GEM_SHOULDER_HEIGHT, GEM_PEAK_HEIGHT, GEM_BEZEL_EXPANSION,
    HEX_BEZEL_EXPANSION, TRIANGLE_BEZEL_EXPANSION, PYRAMID_BEZEL_EXPANSION,
    PARKING_METER_BEZEL_EXPANSION, OCTAGON_BEZEL_EXPANSION,
    TRIANGLE_SHIFT_Y, TRIANGLE_BASE_WIDTH, TRIANGLE_PEAK_HEIGHT,
    PYRAMID_BASE_WIDTH, PYRAMID_PEAK_HEIGHT,
    HEX_MID_WIDTH, HEX_MID_HEIGHT, HEX_TOP_WIDTH, HEX_TOP_HEIGHT,
    TRAPEZOID_TOP_WIDTH, TRAPEZOID_TOP_HEIGHT, TRAPEZOID_BOTTOM_WIDTH,
    STEREO_DIAMOND_WIDTH, STEREO_DIAMOND_HEIGHT, STEREO_DIAMOND_FLAT_WIDTH,
    INTERSECTING_OVERLAY_WIDTH, INTERSECTING_OVERLAY_HEIGHT, INTERSECTING_OVERLAY_SKEW, INTERSECTING_OVERLAY_CUTOUT_RADIUS
)

@dataclass
class BezelRequest:
    cx: float
    cy: float
    w: float
    h: float
    shape: str
    line_width: float
    shrink_px: float = 0

class BezelGeometry:
    @staticmethod
    def get_scaling_params(w, h, shape, line_width):
        """Calculates the radius and global_y_shift for a given shape and container size."""
        shape_key = shape.lower()
        if shape_key not in SHAPE_MULTIPLIERS:
            if shape_key in ["triangle", "pyramid"]: shape_key = "triangle"
            elif shape_key in ["cylinder", "hotdog"]: shape_key = "hotdog" if shape_key == "hotdog" else "cylinder"
            elif shape_key in ["trapezoid", "badge"]: shape_key = "trapezoid"
            else: shape_key = "default"
            
        m_w, m_h = SHAPE_MULTIPLIERS.get(shape_key, SHAPE_MULTIPLIERS["default"])
        y_shift_factor = SHAPE_Y_SHIFTS.get(shape_key, 0.0)

        # SCALING STRATEGY
        avail_w = (w / 2.0) - (line_width / 2) - SAFE_MARGIN
        avail_h = (h) - (line_width / 2) - SAFE_MARGIN 
        
        radius = min(avail_w / m_w, avail_h / m_h)
        global_y_shift = y_shift_factor * radius
        
        return radius, global_y_shift, shape_key

    @staticmethod
    def get_bezel_points(cx, cy, w, h, shape, line_width, shrink_px=0):
        if needle_geo_rs:
            return needle_geo_rs.get_bezel_points(cx, cy, w, h, shape, line_width, shrink_px)

        req = BezelRequest(cx, cy, w, h, shape, line_width, shrink_px)
        return BezelGeometry._calculate_points(req)

    @staticmethod
    def _calculate_points(req: BezelRequest) -> Tuple[List[float], bool]:
        # 1. Get scaling parameters
        radius, global_y_shift, shape_key = BezelGeometry.get_scaling_params(req.w, req.h, req.shape, req.line_width)
        
        # 2. Apply shrink_px to the radius safely
        m_w, m_h = SHAPE_MULTIPLIERS.get(shape_key, SHAPE_MULTIPLIERS["default"])
        radius -= (req.shrink_px / max(m_w, m_h))
        if radius < 1: radius = 1

        handlers = {
            "gem": BezelGeometry._get_gem,
            "super_gem": BezelGeometry._get_super_gem,
            "parking_meter": BezelGeometry._get_parking_meter,
            "octagon": BezelGeometry._get_octagon,
            "triangle": BezelGeometry._get_triangle,
            "pyramid": BezelGeometry._get_pyramid,
            "cylinder": BezelGeometry._get_hotdog_cylinder,
            "hotdog": BezelGeometry._get_hotdog_cylinder,
            "hex": BezelGeometry._get_hex,
            "squectangle": BezelGeometry._get_squectangle,
            "squimonde": BezelGeometry._get_squimonde,
            "squircle": BezelGeometry._get_squircle,
            "trapezoid": BezelGeometry._get_trapezoid,
            "badge": BezelGeometry._get_trapezoid,
            "crest": BezelGeometry._get_crest,
            "stereo_diamond": BezelGeometry._get_stereo_diamond,
            "intersecting_overlay": BezelGeometry._get_intersecting_overlay,
        }

        handler = handlers.get(shape_key)
        if not handler:
            return [], False

        pts_user, is_smooth = handler(radius, global_y_shift, shape_key)

        flat_pts = []
        for x, y in pts_user:
            flat_pts.append(req.cx + x)
            flat_pts.append(req.cy - y) 
            
        return flat_pts, is_smooth

    @staticmethod
    def _get_gem(radius, global_y_shift, shape_key):
        gem_rad = radius * GEM_BEZEL_EXPANSION
        pts = [
            (0, GEM_BASE_HEIGHT * gem_rad + global_y_shift),                        
            (GEM_WIDTH_FACTOR * gem_rad, GEM_BASE_HEIGHT * gem_rad + global_y_shift),             
            (GEM_SHOULDER_WIDTH * gem_rad, GEM_SHOULDER_HEIGHT * gem_rad + global_y_shift),  
            (0, GEM_PEAK_HEIGHT * gem_rad + global_y_shift),             
            (-GEM_SHOULDER_WIDTH * gem_rad, GEM_SHOULDER_HEIGHT * gem_rad + global_y_shift), 
            (-GEM_WIDTH_FACTOR * gem_rad, GEM_BASE_HEIGHT * gem_rad + global_y_shift)             
        ]
        return pts, False

    @staticmethod
    def _get_super_gem(radius, global_y_shift, shape_key):
        gem_rad = radius * GEM_BEZEL_EXPANSION
        pts = [
            (0, -(GEM_BASE_HEIGHT * gem_rad) + global_y_shift),                        
            (GEM_WIDTH_FACTOR * gem_rad, -(GEM_BASE_HEIGHT * gem_rad) + global_y_shift),             
            (GEM_SHOULDER_WIDTH * gem_rad, -(GEM_SHOULDER_HEIGHT * gem_rad) + global_y_shift),  
            (0, -(GEM_PEAK_HEIGHT * gem_rad) + global_y_shift),             
            (-GEM_SHOULDER_WIDTH * gem_rad, -(GEM_SHOULDER_HEIGHT * gem_rad) + global_y_shift), 
            (-GEM_WIDTH_FACTOR * gem_rad, -(GEM_BASE_HEIGHT * gem_rad) + global_y_shift)             
        ]
        return pts, False

    @staticmethod
    def _get_parking_meter(radius, global_y_shift, shape_key):
        pm_rad = radius * PARKING_METER_BEZEL_EXPANSION
        w_val = TRIANGLE_BASE_WIDTH * pm_rad
        h_val = TRIANGLE_PEAK_HEIGHT * pm_rad
        arc_radius = math.sqrt(w_val**2 + h_val**2)
        ang_start = math.atan2(h_val, w_val)
        ang_end = math.atan2(h_val, -w_val)
        pts = [(0, 0 + global_y_shift)] 
        steps = 20
        for i in range(steps + 1):
            ang = ang_start + (ang_end - ang_start) * (i / steps)
            px = arc_radius * math.cos(ang)
            py = arc_radius * math.sin(ang) + global_y_shift
            pts.append((px, py))
        return pts, False

    @staticmethod
    def _get_octagon(radius, global_y_shift, shape_key):
        oct_rad = radius * OCTAGON_BEZEL_EXPANSION
        pts = []
        for i in range(8):
            ang = math.radians(22.5 + i * 45)
            px = oct_rad * math.cos(ang)
            py = oct_rad * math.sin(ang) + global_y_shift
            pts.append((px, py))
        return pts, False

    @staticmethod
    def _get_triangle(radius, global_y_shift, shape_key):
        tri_rad = radius * TRIANGLE_BEZEL_EXPANSION
        pts = [
            (0, 0 + global_y_shift),                                   
            (TRIANGLE_BASE_WIDTH * tri_rad, TRIANGLE_PEAK_HEIGHT * tri_rad + global_y_shift),  
            (-TRIANGLE_BASE_WIDTH * tri_rad, TRIANGLE_PEAK_HEIGHT * tri_rad + global_y_shift)  
        ]
        return pts, False

    @staticmethod
    def _get_pyramid(radius, global_y_shift, shape_key):
        py_rad = radius * PYRAMID_BEZEL_EXPANSION
        pts = [
            (0, PYRAMID_PEAK_HEIGHT * py_rad + global_y_shift),      
            (PYRAMID_BASE_WIDTH * py_rad, 0 + global_y_shift),       
            (-PYRAMID_BASE_WIDTH * py_rad, 0 + global_y_shift)       
        ]
        return pts, False

    @staticmethod
    def _get_hotdog_cylinder(radius, global_y_shift, shape_key):
        if shape_key == "hotdog":
            w_straight = HOTDOG_WIDTH_STRAIGHT * radius
            r_cap = HOTDOG_CAP_RADIUS * radius 
            cap_center_y = HOTDOG_CAP_CENTER_Y * radius
        else:
            w_straight = CYLINDER_WIDTH_STRAIGHT * radius
            r_cap = CYLINDER_CAP_RADIUS * radius 
            cap_center_y = CYLINDER_CAP_CENTER_Y * radius
        
        pts = []
        pts.append((0, 0 + global_y_shift)) 
        pts.append((w_straight, 0 + global_y_shift))
        steps = CYLINDER_STEPS
        for i in range(steps+1):
            ang = math.radians(-90 + (180 * i/steps))
            px = (w_straight) + (r_cap * math.cos(ang))
            py = (cap_center_y) + (r_cap * math.sin(ang))
            pts.append((px, py + global_y_shift))
        for i in range(steps+1):
            ang = math.radians(90 + (180 * i/steps))
            px = (-w_straight) + (r_cap * math.cos(ang))
            py = (cap_center_y) + (r_cap * math.sin(ang))
            pts.append((px, py + global_y_shift))
        pts.append((0, 0 + global_y_shift))
        return pts, False

    @staticmethod
    def _get_hex(radius, global_y_shift, shape_key):
        hex_rad = radius * HEX_BEZEL_EXPANSION
        pts = [
            (0, 0 + global_y_shift),
            (HEX_TOP_WIDTH * hex_rad, 0 + global_y_shift),
            (HEX_MID_WIDTH * hex_rad, HEX_MID_HEIGHT * hex_rad + global_y_shift),
            (HEX_TOP_WIDTH * hex_rad, HEX_TOP_HEIGHT * hex_rad + global_y_shift),
            (-HEX_TOP_WIDTH * hex_rad, HEX_TOP_HEIGHT * hex_rad + global_y_shift),
            (-HEX_MID_WIDTH * hex_rad, HEX_MID_HEIGHT * hex_rad + global_y_shift),
            (-HEX_TOP_WIDTH * hex_rad, 0 + global_y_shift)
        ]
        return pts, False

    @staticmethod
    def _get_squectangle(radius, global_y_shift, shape_key):
        pts = []
        n = SQUIRCLE_N
        w_sq = SQUECTANGLE_WIDTH_FACTOR * radius
        h_sq = SQUECTANGLE_HEIGHT_FACTOR * radius
        steps = SQUIRCLE_STEPS
        for i in range(steps + 1):
            t = -math.pi/2 + (2 * math.pi * i / steps)
            c, s = math.cos(t), math.sin(t)
            x = w_sq * (1 if c>=0 else -1) * (abs(c)**(2/n))
            y_raw = h_sq * (1 if s>=0 else -1) * (abs(s)**(2/n))
            pts.append((x, y_raw + h_sq + global_y_shift))
        return pts, True

    @staticmethod
    def _get_squimonde(radius, global_y_shift, shape_key):
        pts = []
        n = SQUIRCLE_N
        w_sq = SQUIRCLE_WIDTH_FACTOR * radius
        h_sq = SQUIRCLE_HEIGHT_FACTOR * radius
        steps = SQUIRCLE_STEPS
        rot_angle = math.pi / 4
        cos_r = math.cos(rot_angle)
        sin_r = math.sin(rot_angle)
        for i in range(steps + 1):
            t = -math.pi/2 + (2 * math.pi * i / steps)
            c, s = math.cos(t), math.sin(t)
            x_raw = w_sq * (1 if c>=0 else -1) * (abs(c)**(2/n))
            y_raw = h_sq * (1 if s>=0 else -1) * (abs(s)**(2/n))
            x_rot = x_raw * cos_r - y_raw * sin_r
            y_rot = x_raw * sin_r + y_raw * cos_r
            pts.append((x_rot, y_rot + h_sq + global_y_shift))
        return pts, True

    @staticmethod
    def _get_squircle(radius, global_y_shift, shape_key):
        pts = []
        n = SQUIRCLE_N
        w_sq = SQUIRCLE_WIDTH_FACTOR * radius
        h_sq = SQUIRCLE_HEIGHT_FACTOR * radius
        steps = SQUIRCLE_STEPS
        for i in range(steps + 1):
            t = -math.pi/2 + (2 * math.pi * i / steps)
            c, s = math.cos(t), math.sin(t)
            x = w_sq * (1 if c>=0 else -1) * (abs(c)**(2/n))
            y_raw = h_sq * (1 if s>=0 else -1) * (abs(s)**(2/n))
            pts.append((x, y_raw + h_sq + global_y_shift))
        return pts, True

    @staticmethod
    def _get_trapezoid(radius, global_y_shift, shape_key):
        pts = [
            (0, 0 + global_y_shift),
            (TRAPEZOID_BOTTOM_WIDTH * radius, 0 + global_y_shift),
            (TRAPEZOID_TOP_WIDTH * radius, TRAPEZOID_TOP_HEIGHT * radius + global_y_shift),
            (-TRAPEZOID_TOP_WIDTH * radius, TRAPEZOID_TOP_HEIGHT * radius + global_y_shift),
            (-TRAPEZOID_BOTTOM_WIDTH * radius, 0 + global_y_shift)
        ]
        return pts, False

    @staticmethod
    def _get_crest(radius, global_y_shift, shape_key):
        pts = [(0, 0 + global_y_shift)]
        curve_steps = CREST_CURVE_STEPS
        for i in range(1, curve_steps + 1):
            y_u = CREST_BOTTOM_HEIGHT_FACTOR * radius * (i / curve_steps)
            x_u = CREST_TOP_WIDTH_FACTOR * radius * math.sqrt(y_u / (CREST_BOTTOM_HEIGHT_FACTOR * radius))
            pts.append((x_u, y_u + global_y_shift))
        pts.append((CREST_TOP_WIDTH_FACTOR * radius, CREST_TOP_HEIGHT_FACTOR * radius + global_y_shift))
        pts.append((-CREST_TOP_WIDTH_FACTOR * radius, CREST_TOP_HEIGHT_FACTOR * radius + global_y_shift))
        pts.append((-CREST_TOP_WIDTH_FACTOR * radius, CREST_BOTTOM_HEIGHT_FACTOR * radius + global_y_shift))
        for i in range(curve_steps - 1, -1, -1):
            y_u = CREST_BOTTOM_HEIGHT_FACTOR * radius * (i / curve_steps)
            if y_u < 0.01: y_u = 0
            x_u = CREST_TOP_WIDTH_FACTOR * radius * math.sqrt(y_u / (CREST_BOTTOM_HEIGHT_FACTOR * radius))
            pts.append((-x_u, y_u + global_y_shift))
        return pts, False

    @staticmethod
    def _get_stereo_diamond(radius, global_y_shift, shape_key):
        w_sd = STEREO_DIAMOND_WIDTH * radius
        h_sd = STEREO_DIAMOND_HEIGHT * radius
        fw = STEREO_DIAMOND_FLAT_WIDTH * radius
        pts = [
            (fw, h_sd + global_y_shift),
            (w_sd, 0 + global_y_shift),
            (fw, -h_sd + global_y_shift),
            (-fw, -h_sd + global_y_shift),
            (-w_sd, 0 + global_y_shift),
            (-fw, h_sd + global_y_shift)
        ]
        return pts, False

    @staticmethod
    def _get_intersecting_overlay(radius, global_y_shift, shape_key):
        w_io = INTERSECTING_OVERLAY_WIDTH * radius
        h_io = INTERSECTING_OVERLAY_HEIGHT * radius
        skew = INTERSECTING_OVERLAY_SKEW * radius
        cr = INTERSECTING_OVERLAY_CUTOUT_RADIUS * radius
        pts = [
            (-w_io + skew, h_io + global_y_shift),
            (w_io + skew, h_io + global_y_shift),
            (w_io - skew, -h_io + global_y_shift)
        ]
        steps = 20
        for i in range(steps + 1):
            ang = math.pi + (math.pi * i / steps)
            px = (w_io - skew) + cr * math.cos(ang)
            py = (-h_io) + cr * math.sin(ang) + global_y_shift
            pts.append((px, py))
        pts.extend([
            (-w_io - skew, -h_io + global_y_shift)
        ])
        return pts, False
