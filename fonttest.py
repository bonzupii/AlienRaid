import tcod as libtcod
# -*- coding: utf-8 -*-
#
#  fonttest.py
#  
#  Copyright 2019 Bonzu <bonzupii@protonmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#  
# 
print("AlienRaid Copyright (C) 2019  Bonzu <bonzupii@protonmail.com>\nThis program comes with ABSOLUTELY NO WARRANTY.\nThis is free software, and you are welcome to redistribute it under\ncertain conditions.\nSee enclosed LICENSE.md for details.")
print("\nA file for developers to use to test and keep track of icons in the fontmap.\n")
def main():
	screen_width = 5
	screen_height = 35

	libtcod.console_set_custom_font('alienraid12x12.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
	libtcod.console_init_root(screen_width, screen_height, 'Alien Raid Icon Tracker', False)

	while not libtcod.console_is_window_closed():
		libtcod.console_set_default_foreground(0, libtcod.white)
		#COLUMN 1
		libtcod.console_put_char(0, 1, 1, 196, libtcod.BKGND_NONE) #KANGA
		libtcod.console_put_char(0, 1, 3, 179, libtcod.BKGND_NONE) #JOEY
		libtcod.console_put_char(0, 1, 5, 191, libtcod.BKGND_NONE) #DINGO
		libtcod.console_put_char(0, 1, 7, 218, libtcod.BKGND_NONE) #TENTACLAWS/TENTACRUEL
		libtcod.console_put_char(0, 1, 9, 217, libtcod.BKGND_NONE) #ENERGY SHIELD
		libtcod.console_put_char(0, 1, 11, 192, libtcod.BKGND_NONE) #ALUMINITE TENTASLEEVE
		libtcod.console_put_char(0, 1, 13, 180, libtcod.BKGND_NONE) #CORPSE
		libtcod.console_put_char(0, 1, 15, 195, libtcod.BKGND_NONE) #MED KIT
		libtcod.console_put_char(0, 1, 17, 193, libtcod.BKGND_NONE) #GRENADE
		libtcod.console_put_char(0, 1, 19, 194, libtcod.BKGND_NONE) #SHOCK CHARGE
		libtcod.console_put_char(0, 1, 21, 197, libtcod.BKGND_NONE) #ALIEN
		libtcod.console_put_char(0, 1, 23, 205, libtcod.BKGND_NONE) #TRAIL
		libtcod.console_put_char(0, 1, 25, 186, libtcod.BKGND_NONE) #GOANNA
		libtcod.console_put_char(0, 1, 27, 187, libtcod.BKGND_NONE) #RAY GUN
		libtcod.console_put_char(0, 1, 29, 201, libtcod.BKGND_NONE) #KILLER BEE
		libtcod.console_put_char(0, 1, 31, 188, libtcod.BKGND_NONE) #WHIPPY WILLOW TWIG
		libtcod.console_put_char(0, 1, 33, 200, libtcod.BKGND_NONE) #HAT
		#COLUMN 2
		libtcod.console_put_char(0, 3, 1, 185, libtcod.BKGND_NONE) #CHEST_PLATE
		libtcod.console_put_char(0, 3, 3, 204, libtcod.BKGND_NONE) #NECK BRACER
		libtcod.console_put_char(0, 3, 5, 202, libtcod.BKGND_NONE) #
		libtcod.console_put_char(0, 3, 7, 203, libtcod.BKGND_NONE) #
		libtcod.console_put_char(0, 3, 9, 206, libtcod.BKGND_NONE) #
		libtcod.console_put_char(0, 3, 11, 176, libtcod.BKGND_NONE) # WALL1
		libtcod.console_put_char(0, 3, 13, 177, libtcod.BKGND_NONE) # WALL2
		libtcod.console_put_char(0, 3, 15, 178, libtcod.BKGND_NONE) #
		libtcod.console_put_char(0, 3, 17, 25, libtcod.BKGND_NONE) #
		libtcod.console_put_char(0, 3, 19, 26, libtcod.BKGND_NONE) #
		libtcod.console_put_char(0, 3, 21, 27, libtcod.BKGND_NONE) #
		libtcod.console_put_char(0, 3, 23, 30, libtcod.BKGND_NONE) #
		libtcod.console_put_char(0, 3, 25, 31, libtcod.BKGND_NONE) #
		libtcod.console_put_char(0, 3, 27, 16, libtcod.BKGND_NONE) #
		libtcod.console_put_char(0, 3, 29, 17, libtcod.BKGND_NONE) #
		libtcod.console_put_char(0, 3, 31, 29, libtcod.BKGND_NONE) #
		libtcod.console_put_char(0, 3, 33, 18, libtcod.BKGND_NONE) #
		libtcod.console_flush()

		key = libtcod.console_check_for_keypress()

		if key.vk == libtcod.KEY_ESCAPE:
			return True


if __name__ == '__main__':
	main()
	
# TCOD_CHAR_HLINE = 196 #
# TCOD_CHAR_VLINE = 179 #
# TCOD_CHAR_NE = 191 #
# TCOD_CHAR_NW = 218 #
# TCOD_CHAR_SE = 217 # 
# TCOD_CHAR_SW = 192 #
# TCOD_CHAR_TEEW = 180 #
# TCOD_CHAR_TEEE = 195 #
# TCOD_CHAR_TEEN = 193 #
# TCOD_CHAR_TEES = 194 #
# TCOD_CHAR_CROSS = 197 #
# TCOD_CHAR_DHLINE = 205 #
# TCOD_CHAR_DVLINE = 186 #
# TCOD_CHAR_DNE = 187 #
# TCOD_CHAR_DNW = 201 #
# TCOD_CHAR_DSE = 188 #
# TCOD_CHAR_DSW = 200 #
# TCOD_CHAR_DTEEW = 185 #
# TCOD_CHAR_DTEEE = 204 #
# TCOD_CHAR_DTEEN = 202 #
# TCOD_CHAR_DTEES = 203 #
# TCOD_CHAR_DCROSS = 206 #
# TCOD_CHAR_BLOCK1 = 176 #
# TCOD_CHAR_BLOCK2 = 177 #
# TCOD_CHAR_BLOCK3 = 178 #
# TCOD_CHAR_ARROW_N = 24 ##SKIPPED
# TCOD_CHAR_ARROW_S = 25 #
# TCOD_CHAR_ARROW_E = 26 #
# TCOD_CHAR_ARROW_W = 27 #
# TCOD_CHAR_ARROW2_N = 30 #
# TCOD_CHAR_ARROW2_S = 31 #
# TCOD_CHAR_ARROW2_E = 16 #
# TCOD_CHAR_ARROW2_W = 17 #
# TCOD_CHAR_DARROW_H = 29 #
# TCOD_CHAR_DARROW_V = 18 #
# TCOD_CHAR_CHECKBOX_UNSET = 224
# TCOD_CHAR_CHECKBOX_SET = 225
# TCOD_CHAR_RADIO_UNSET = 9
# TCOD_CHAR_RADIO_SET = 10
# TCOD_CHAR_SUBP_NW = 226
# TCOD_CHAR_SUBP_NE = 227
# TCOD_CHAR_SUBP_N = 228
# TCOD_CHAR_SUBP_SE = 229
# TCOD_CHAR_SUBP_DIAG = 230
# TCOD_CHAR_SUBP_E = 231
# TCOD_CHAR_SUBP_SW = 232
# TCOD_CHAR_SMILIE = 1
# TCOD_CHAR_SMILIE_INV = 2
# TCOD_CHAR_HEART = 3
# TCOD_CHAR_DIAMOND = 4
# TCOD_CHAR_CLUB = 5
# TCOD_CHAR_SPADE = 6
# TCOD_CHAR_BULLET = 7
# TCOD_CHAR_BULLET_INV = 8
# TCOD_CHAR_MALE = 11
# TCOD_CHAR_FEMALE = 12
# TCOD_CHAR_NOTE = 13
# TCOD_CHAR_NOTE_DOUBLE = 14
# TCOD_CHAR_LIGHT = 15
# TCOD_CHAR_EXCLAM_DOUBLE = 19
# TCOD_CHAR_PILCROW = 20
# TCOD_CHAR_SECTION = 21
# TCOD_CHAR_POUND = 156
# TCOD_CHAR_MULTIPLICATION = 158
# TCOD_CHAR_FUNCTION = 159
# TCOD_CHAR_RESERVED = 169
# TCOD_CHAR_HALF = 171
# TCOD_CHAR_ONE_QUARTER = 172
# TCOD_CHAR_COPYRIGHT = 184
# TCOD_CHAR_CENT = 189
# TCOD_CHAR_YEN = 190
# TCOD_CHAR_CURRENCY = 207
# TCOD_CHAR_THREE_QUARTERS = 243
# TCOD_CHAR_DIVISION = 246
# TCOD_CHAR_GRADE = 248
# TCOD_CHAR_UMLAUT = 249
# TCOD_CHAR_POW1 = 251
# TCOD_CHAR_POW3 = 252
# TCOD_CHAR_POW2 = 253
# TCOD_CHAR_BULLET_SQUARE = 254
