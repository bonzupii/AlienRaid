import libtcodpy as libtcod


def main():
	screen_width = 80
	screen_height = 50

	libtcod.console_set_custom_font('arial12x12.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
	libtcod.console_init_root(screen_width, screen_height, 'libtcod tutorial revised', False)

	while not libtcod.console_is_window_closed():
		libtcod.console_set_default_foreground(0, libtcod.white)
		libtcod.console_put_char(0, 1, 1, 196, libtcod.BKGND_NONE) #KANGA
		libtcod.console_put_char(0, 1, 3, 179, libtcod.BKGND_NONE) #JOEY
		libtcod.console_put_char(0, 1, 5, 191, libtcod.BKGND_NONE) #DINGO
		libtcod.console_put_char(0, 1, 7, 218, libtcod.BKGND_NONE) #TENTACLAWS/TENTACRUEL
		libtcod.console_put_char(0, 1, 9, 217, libtcod.BKGND_NONE) #ENERGY SHEILD
		libtcod.console_put_char(0, 1, 11, 192, libtcod.BKGND_NONE) #ALUMINITE TENTASLEEVE
		libtcod.console_put_char(0, 1, 13, 180, libtcod.BKGND_NONE) #CORPSE
		libtcod.console_put_char(0, 1, 15, 195, libtcod.BKGND_NONE) #MED KIT
		libtcod.console_put_char(0, 1, 17, 193, libtcod.BKGND_NONE) #GRENADE
		libtcod.console_put_char(0, 1, 19, 194, libtcod.BKGND_NONE) #SHOCK CHARGE
		libtcod.console_put_char(0, 1, 21, 197, libtcod.BKGND_NONE) #ALIEN
		libtcod.console_put_char(0, 1, 23, 205, libtcod.BKGND_NONE) #TRAIL
		libtcod.console_put_char(0, 1, 25, 186, libtcod.BKGND_NONE) #GOANNA
		libtcod.console_put_char(0, 1, 25, 187, libtcod.BKGND_NONE) #RAY GUN
		libtcod.console_put_char(0, 1, 25, 201, libtcod.BKGND_NONE) #KILLER BEE
		
		libtcod.console_flush()

		key = libtcod.console_check_for_keypress()

		if key.vk == libtcod.KEY_ESCAPE:
			return True


if __name__ == '__main__':
	main()
