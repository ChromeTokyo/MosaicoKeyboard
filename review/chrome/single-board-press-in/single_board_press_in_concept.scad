// Visual comparison only, 2026-09-23. Not a footprint, approved geometry, or manufacturing file.
// Reuses assumed Mosaico envelope and H2 row direction from mech-module 42172f7.
// Explores the user's press-in (screen-normal -Z) single-XY-board concept.
$fn = 48;
SHOW_HOST = true;
SHOW_DOCK = true;
EXPLODE = 0;
ROWS = 8; // 8 => 16 pads; 6 => 12-pad minimum connectivity concept
M_W = 45.19;
M_H = 45.19;
M_T = 11.48;
BX0 = -36.0;
BX1 = -23.8;
BY0 = -20.0;
BY1 = 20.0;
BZ0 = -6.6;
BT = 1.6;
PAD_PITCH = 2.54;
PAD_D = 2.0;
PAD_X0 = -33.0;
PAD_Y0 = -(ROWS-1)*PAD_PITCH/2;
module host() {
  color([0.65,0.75,0.95,0.20])
  translate([-M_W/2,-M_H/2,-M_T/2]) cube([M_W,M_H,M_T]);
}
module board() {
  color([0.00,0.27,0.06])
  translate([BX0,BY0,BZ0]) cube([BX1-BX0,BY1-BY0,BT]);
}
module header() {
  // Simplified candidate 2x10 right-angle connector envelope; not a selected part.
  color([0.14,0.14,0.16])
  translate([-27.6,-12.7,BZ0+BT]) cube([4.1,25.4,7.5]);
  color([0.9,0.62,0.04])
  for (j=[0:9], zrow=[-1.27,1.27]) {
    yy = -11.43 + j*2.54;
    translate([-23.5,yy-0.3,zrow-0.3]) cube([5.9,0.6,0.6]);
  }
}
module eeprom() {
  color([0.04,0.04,0.06])
  translate([-33.7,13.0,BZ0+BT]) cube([3.8,5.0,1.7]);
}
module pads() {
  color([0.95,0.68,0.05])
  for (col=[0:1], row=[0:ROWS-1])
    translate([PAD_X0+col*PAD_PITCH,PAD_Y0+row*PAD_PITCH,BZ0-0.035])
      cylinder(h=0.07,d=PAD_D);
}
module dock_shifted() {
  translate([0,0,-EXPLODE]) {
    color([0.18,0.32,0.54,0.55])
    translate([-38.0,-21.5,-12.0]) cube([16.3,43.0,1.5]);
    for (col=[0:1], row=[0:ROWS-1]) {
      xx=PAD_X0+col*PAD_PITCH;
      yy=PAD_Y0+row*PAD_PITCH;
      color([0.54,0.59,0.64])
        translate([xx,yy,-10.5]) cylinder(h=3.2,d=1.1);
      color([0.95,0.71,0.10])
        translate([xx,yy,-7.3]) cylinder(h=0.7,d=0.9);
    }
  }
}
if (SHOW_HOST) host();
board(); header(); eeprom(); pads();
if (SHOW_DOCK) dock_shifted();
