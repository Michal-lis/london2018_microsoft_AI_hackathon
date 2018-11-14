import argparse
import atexit
import locale
import platform
import threading
import time
import json

from gui import null_visuals
from gui import battleships_visuals
from gui import noughts_and_crosses_visuals
from gui import twist_cube_visuals
from gui import sliding_puzzle_visuals
from gui import travelling_salesdrone_visuals
from gui import predictive_text_visuals
from gui import blurry_word_visuals
from gui import mastermind_visuals
from gui import warehouse_logistics_visuals
from gui import four_in_a_row_visuals
from gui import who_is_who_visuals
from gui import reversing_stones_visuals
from gui import checkers_visuals
from gui import go_visuals
from gui import lexico_visuals
from gui import dominoes_visuals

from bots import mover

import requests

from tkinter import Tk, Label, Button, Text, W, E, Entry, Frame, Listbox, Checkbutton, Message, BooleanVar, messagebox, ttk

# Platforms
WINDOWS = (platform.system() == "Windows")
LINUX = (platform.system() == "Linux")
MAC = (platform.system() == "Darwin")

CANCEL_GAME_TEXT = 'Cancel Game'

API_CALL_HEADERS = {'Content-Type': 'application/json'}

GAME_STYLE_LISTBOX_ACTIVE_STYLE = 'none'

GAME_STYLE_LISTBOX_DEFAULT_SELECTION = 0

DISABLED = 'disable'
ENABLED = 'normal'


class DemoClient(Frame):
    def __init__(self, tk, args):
        Frame.__init__(self, tk)
        locale.setlocale(locale.LC_ALL, '')  # empty string for platform's default settings
        self.master = tk
        self.config = json.load(open('config.json', 'r'))
        self.config['COMBOBOX_INDEX'] = sorted(self.config['COMBOBOX_INDEX'], key=lambda x: x[0])
        self.game_type = int(args.gametype) if args.gametype else self.config["DEFAULT_GAME_TYPE_ID"]
        tk.title(self.config["APP_TITLE"])
        tk.resizable(False, False)
        self.get_icon()
        atexit.register(self.cancel_game)

        # Init class data fields that we use for storing info that we need for using the API
        self.bot_id = None
        self.bot_password = None
        self.logged_in = False
        self.game_style_ids = []
        self.gameChips = 0
        self.gameDeals = 0
        self.gameStake = 0
        self.gamePrize = 0
        self.player_key = None
        self.play_again = BooleanVar()
        self.do_not_play_same_user = BooleanVar()
        self.close_after_game = False
        self.game_cancelled = False
        self.in_game = False

        self.topFrame = Frame(tk, padx=12, pady=12)
        self.middleFrame = Frame(tk, padx=12)
        self.middleFrameLeft = Frame(self.middleFrame)
        self.middleFrameRight = Frame(self.middleFrame)
        self.middleFrameRighter = Frame(self.middleFrame)

        self.topFrame.grid(row=0, sticky=W + E)

        self.middleFrame.grid(row=1, sticky=W)
        self.middleFrameLeft.grid(row=1, column=0)
        self.middleFrameRight.grid(row=1, column=1)
        self.middleFrameRighter.grid(row=1, column=2)

        # ===================================
        # Create form elements

        # Top Frame Elements
        self.botNameLabel = Label(self.topFrame, text="Bot Name:")
        self.bot_id_entry = Entry(self.topFrame)
        self.bot_id_entry.bind('<Return>', self.log_in_if_not)
        self.bot_id_entry.focus()
        self.passwordLabel = Label(self.topFrame, text="Password:")
        self.bot_password_entry = Entry(self.topFrame, show='*')
        self.bot_password_entry.bind('<Return>', self.log_in_if_not)
        self.log_in_out_button = Button(self.topFrame, text="Login", command=self.log_in_out_clicked)

        self.balanceLabel = Label(self.topFrame, text="Bot Balance:")
        self.balance = Label(self.topFrame, text="0")
        self.close_button = Button(self.topFrame, text="Close", padx=2, command=tk.destroy)

        # Middle Frame Elements
        # Middle Frame LEFT Elements
        self.gameTypeCmb = ttk.Combobox(self.middleFrameLeft, state="disabled", values=tuple((game[0]) for game in self.config['COMBOBOX_INDEX']))
        if self.game_type != self.config['NULL_GAME_TYPE_ID']:
            index = [i for i in range(len(self.config['COMBOBOX_INDEX'])) if self.config['COMBOBOX_INDEX'][i][1] == self.game_type][0]
            self.gameTypeCmb.current(index)  # Default selection matches default game type id
        self.gameTypeCmb.bind("<<ComboboxSelected>>", self.game_type_selected)

        self.gameStyleLabel = Label(self.middleFrameLeft, font=(None, 18), pady=0, text="Game Style Selection")

        self.opponentLabel = Label(self.middleFrameLeft, text="Specify Opponent (optional):")
        self.specify_opponent_cmb = ttk.Combobox(self.middleFrameLeft, values=self.config['AVAILABLE_OPPONENTS'])

        self.do_not_play_same_user_check = Checkbutton(self.middleFrameLeft,
                                                       text='Don\'t play another bot in same user account as me',
                                                       var=self.do_not_play_same_user)

        self.game_styles_listbox = Listbox(self.middleFrameLeft, background='#FFFFFF', height=8)
        self.game_styles_listbox.bind('<Double-1>', self.find_game_double_clicked)
        self.game_styles_listbox.bind('<Return>', self.find_game_double_clicked)  # Not a double click but we want it to do the same thing

        self.refresh_game_styles_button = Button(self.middleFrameLeft, text="Refresh Game Styles",
                                                 command=self.refresh_game_styles_clicked)

        self.thinkingTimeLabel = Label(self.middleFrameLeft, text="Add \"Thinking Time\" (ms):")
        self.thinking_time_entry = Entry(self.middleFrameLeft)

        self.auto_play_next_game_check = Checkbutton(self.middleFrameLeft, text='Play another game when complete',
                                                     var=self.play_again)

        self.cancel_stop_game_button = Button(self.middleFrameLeft, text=CANCEL_GAME_TEXT,
                                              command=self.cancel_stop_game_clicked)
        self.find_game_button = Button(self.middleFrameLeft, text="Find Game", command=self.find_game_clicked)

        self.resultText = Message(self.middleFrameLeft, width=300,
                                  text="This is where the informational messages will appear")
        self.spacerLabel = Label(self.middleFrameLeft, text=" ")

        # Middle Frame RIGHT Elements

        self.gameTitleLabel = Label(self.middleFrameRight, text="Game Title")
        self.gameTitleText = Text(self.middleFrameRight, height=3, background='white', spacing1=3, pady=0)

        self.player = None  # Initialise as none before updating in create_visuals()
        self.opponent = None  # Initialise as none before updating in create_visuals()
        self.create_visuals()

        self.gameActionLabel = Label(self.middleFrameRight, text="")

        # ===================================
        # Set initial element states

        self.set_gamestyle_controls_states(DISABLED)
        self.cancel_stop_game_button.config(state=DISABLED)
        self.game_styles_listbox.config(background='white')
        self.thinking_time_entry.insert(0, 100)
        self.gameTitleText.config(state=DISABLED)
        self.set_balance(0)
        self.gameTitleText.tag_configure("center", justify='center')
        self.gameTitleText.tag_configure("bold", font='-weight bold')

        # ===================================
        # Form Layout

        # Top Frame Form Layout
        self.topFrame.grid_rowconfigure(0, weight=1)
        self.botNameLabel.grid(row=0, column=0, sticky=E)
        self.bot_id_entry.grid(row=0, column=1, sticky=W)
        self.passwordLabel.grid(row=0, column=2, sticky=E)
        self.bot_password_entry.grid(row=0, column=3, sticky=W)
        self.log_in_out_button.grid(row=0, column=4, sticky=E)
        self.topFrame.grid_columnconfigure(5, weight=1)
        self.balanceLabel.grid(row=0, column=5, sticky=E)
        self.balance.grid(row=0, column=6, sticky=W)
        self.close_button.grid(row=0, column=7, sticky=E, padx=(50, 0))

        # Middle Frame Form Layout
        self.middleFrame.grid_rowconfigure(0, weight=1)
        self.gameTypeCmb.grid(row=0, column=0, columnspan=1, sticky=W + E)
        self.gameStyleLabel.grid(row=1, column=0, columnspan=1, sticky=W + E)
        self.spacerLabel.grid(row=1, column=2, sticky=E)

        self.opponentLabel.grid(row=2, column=0, sticky=W, pady=4)
        self.specify_opponent_cmb.grid(row=2, column=0, sticky=E, pady=4)

        self.do_not_play_same_user_check.grid(row=3, column=0, columnspan=1, sticky='we', pady=4)
        self.game_styles_listbox.grid(row=4, column=0, columnspan=1, sticky='we', pady=4)
        self.find_game_button.grid(row=5, column=0, pady=4, sticky=W)
        self.refresh_game_styles_button.grid(row=5, column=0, columnspan=1, sticky='', pady=4)
        self.cancel_stop_game_button.grid(row=5, column=0, sticky=E)

        self.thinkingTimeLabel.grid(row=6, column=0, sticky=W, pady=4)
        self.thinking_time_entry.grid(row=6, column=0, sticky=E, pady=4)

        self.auto_play_next_game_check.grid(row=7, column=0, columnspan=1, sticky=W, pady=4)
        self.resultText.grid(row=9, column=0, columnspan=2, sticky=W, pady=4)
        self.middleFrame.grid_columnconfigure(9, weight=1)

        self.gameTitleLabel.grid(row=0, column=3)
        self.gameTitleText.grid(row=0, column=3, columnspan=2)
        self.gameActionLabel.grid(row=11, column=3, sticky='w')

        if args.botid is not None and args.password is not None:
            self.auto_play(args)

    def auto_play(self, args):
        self.bot_id_entry.insert(0, args.botid)
        self.bot_password_entry.insert(0, args.password)
        self.log_in_out_clicked()
        self.thinking_time_entry.insert(0, args.timeout)
        if args.playanothergame:
            self.auto_play_next_game_check.select()
        if args.dontplaysameuserbot:
            self.do_not_play_same_user_check.select()
        if args.closeaftergame:
            self.close_after_game = True
        if args.gamestyle is not None:
            i = 0
            for i in range(self.game_styles_listbox.size()):
                if args.gamestyle in str(self.game_styles_listbox.get(i)):
                    break
            self.game_styles_listbox.select_set(i, i)
            self.find_game_clicked()

    def log_in_out_clicked(self):
        """Click handler for the 'Login'/'Logout' button."""

        # This means we're logging out
        if self.logged_in:
            self.resultText.config(text='Logged Out')

            self.master.title(self.config["APP_TITLE"] + " (Not Logged In)")

            self.cancel_game()

            self.bot_id = None
            self.bot_password = None
            self.clear_game_title_text()
            self.gameActionLabel.config(text="")
            self.reset_game_styles_listbox()
            self.clear_all_boards()
            self.opponent.delete("all")

            self.log_in_out_button.config(text='Login')

            self.set_login_controls_states(ENABLED)
            self.set_gamestyle_controls_states(DISABLED)
            self.gameTypeCmb.config(state="disabled")

            self.logged_in = False
            self.bot_password_entry.delete(0, 'end')
            self.set_balance(0)

        # This means we're logging in
        else:
            self.bot_id = self.bot_id_entry.get()
            self.bot_password = self.bot_password_entry.get()

            res = self.get_list_of_game_styles()
            if res['Result'] == 'SUCCESS':
                self.resultText.config(text='Logged In')

                game_styles = res['GameStyles']
                self.master.title(self.bot_id + " - " + self.config["APP_TITLE"])

                self.set_login_controls_states(DISABLED)
                self.set_gamestyle_controls_states(ENABLED)
                self.gameTypeCmb.config(state="readonly")

                self.set_game_styles_listbox(game_styles)
                self.set_balance(res['Balance'])

                self.log_in_out_button.config(text='Logout')

                self.logged_in = True

            else:
                messagebox.showerror('Error', 'Invalid login attempt. Please check the username and password entered.')

    def log_in_if_not(self, _):
        if not self.logged_in:
            self.log_in_out_clicked()

    def clear_all_boards(self):
        self.player.clear_board()
        self.opponent.clear_board()
        self.player.delete("all")
        self.opponent.delete("all")
        self.player.myBoard = None
        self.opponent.oppBoard = None

    def set_in_game(self, value):
        self.in_game = value

    def set_game_title_text(self, text, tag):
        self.gameTitleText.config(state=ENABLED)
        self.gameTitleText.insert("end", text, ("center", tag))
        self.gameTitleText.config(state=DISABLED)

    def clear_game_title_text(self):
        self.gameTitleText.config(state=ENABLED)
        self.gameTitleText.delete("1.0", "end")
        self.gameTitleText.config(state=DISABLED)

    def set_login_controls_states(self, state):
        self.bot_id_entry.config(state=state)
        self.bot_password_entry.config(state=state)

    def set_gamestyle_controls_states(self, state):
        self.specify_opponent_cmb.config(state=state)
        self.do_not_play_same_user_check.config(state=state)
        self.game_styles_listbox.config(state=state)
        self.find_game_button.config(state=state)
        self.refresh_game_styles_button.config(state=state)
        self.auto_play_next_game_check.config(state=state)
        self.thinking_time_entry.config(state=state)
        self.opponentLabel.config(state=state)
        self.thinkingTimeLabel.config(state=state)
        self.balanceLabel.config(state=state)
        self.balance.config(state=state)
        self.gameStyleLabel.config(state=state)
        self.game_styles_listbox.config(state=state)
        self.player.config(state=state)
        self.opponent.config(state=state)

    def set_balance(self, balance):
        """Set the balance field"""
        self.balance['text'] = int_with_commas(balance)

    def get_list_of_game_styles(self):
        """Get list of game styles from the server."""

        req = {'BotId': self.bot_id,
               'BotPassword': self.bot_password,
               'GameTypeId': self.game_type}

        url = self.config["BASE_URL"] + self.config["GET_LIST_OF_GAME_STYLES_EXTENSION"]

        return DemoClient.make_api_call(url, req)

    def set_game_styles_listbox(self, game_styles):
        """Set the content of the game styles listbox with a list of GameStyle dictionaries.
        Keyword Arguments:
        game_styles -- The list of GameStyle dictionaries, this should be obtained through get_list_of_game_styles().
        """
        self.reset_game_styles_listbox()
        for index, game_style in enumerate(game_styles):
            if self.game_type == self.config["BATTLESHIPS_GAME_TYPE_ID"]:
                self.game_styles_listbox.insert(index, self.config["BATTLESHIPS_GAME_STYLE_LISTBOX_TEXT"].format(game_style['GameStyleId'],
                                                                                                                 game_style['Stake'],
                                                                                                                 game_style['GameTypeSpecificInfo']['Ships'],
                                                                                                                 game_style['GameTypeSpecificInfo']['Board Size'],
                                                                                                                 game_style['GameTypeSpecificInfo']['Timeout ms'],
                                                                                                                 game_style['GameTypeSpecificInfo']['DealsTotal'],
                                                                                                                 game_style['GameTypeSpecificInfo']['PercentageLand'],
                                                                                                                 game_style['GameTypeSpecificInfo']['RandomLand']))
            elif self.game_type == self.config["NOUGHTS_AND_CROSSES_GAME_TYPE_ID"]:
                self.game_styles_listbox.insert(index, self.config["NOUGHTS_AND_CROSSES_GAME_STYLE_LISTBOX_TEXT"].format(game_style['GameStyleId'],
                                                                                                                         game_style['Stake'],
                                                                                                                         game_style['GameTypeSpecificInfo']['DealsTotal'],
                                                                                                                         game_style['GameTypeSpecificInfo']['Timeout ms']))
            elif self.game_type == self.config["TRAVELLING_SALESDRONE_GAME_TYPE_ID"]:
                self.game_styles_listbox.insert(index, self.config["TRAVELLING_SALESDRONE_GAME_STYLE_LISTBOX_TEXT"].format(game_style['GameStyleId'],
                                                                                                                           game_style['Stake'],
                                                                                                                           game_style['GameTypeSpecificInfo']['TotalCities'],
                                                                                                                           game_style['GameTypeSpecificInfo']['DealLength']))
            elif self.game_type == self.config["PREDICTIVE_TEXT_GAME_TYPE_ID"]:
                self.game_styles_listbox.insert(index, self.config["PREDICTIVE_TEXT_GAME_STYLE_LISTBOX_TEXT"].format(game_style['GameStyleId'],
                                                                                                                     game_style['Stake'],
                                                                                                                     game_style['GameTypeSpecificInfo']['Number of Sentences'],
                                                                                                                     game_style['GameTypeSpecificInfo']['Switched Words Game'],
                                                                                                                     game_style['GameTypeSpecificInfo']['Timeout ms']))
            elif self.game_type == self.config["TWIST_CUBE_GAME_TYPE_ID"]:
                self.game_styles_listbox.insert(index, self.config["TWIST_CUBE_GAME_STYLE_LISTBOX_TEXT"].format(game_style['GameStyleId'],
                                                                                                                game_style['Stake'],
                                                                                                                game_style['GameTypeSpecificInfo']['cubeSize'],
                                                                                                                game_style['GameTypeSpecificInfo']['GameLength']))
            elif self.game_type == self.config["SLIDING_PUZZLE_GAME_TYPE_ID"]:
                self.game_styles_listbox.insert(index, self.config["SLIDING_PUZZLE_GAME_STYLE_LISTBOX_TEXT"].format(game_style['GameStyleId'],
                                                                                                                    game_style['Stake'],
                                                                                                                    game_style['GameTypeSpecificInfo']['RowSize'],
                                                                                                                    game_style['GameTypeSpecificInfo']['ColumnSize'],
                                                                                                                    game_style['GameTypeSpecificInfo']['TimeLimit']))
            elif self.game_type == self.config["BLURRY_WORD_GAME_TYPE_ID"]:
                self.game_styles_listbox.insert(index, self.config["BLURRY_WORD_GAME_STYLE_LISTBOX_TEXT"].format(game_style['GameStyleId'],
                                                                                                                 game_style['Stake'],
                                                                                                                 game_style['GameTypeSpecificInfo']['NumImages'],
                                                                                                                 game_style['GameTypeSpecificInfo']['GameLength']))
            elif self.game_type == self.config["MASTERMIND_GAME_TYPE_ID"]:
                self.game_styles_listbox.insert(index, self.config["MASTERMIND_GAME_STYLE_LISTBOX_TEXT"].format(game_style['GameStyleId'],
                                                                                                                game_style['Stake'],
                                                                                                                game_style['GameTypeSpecificInfo']['NumPegs'],
                                                                                                                game_style['GameTypeSpecificInfo']['NumColours'],
                                                                                                                game_style['GameTypeSpecificInfo']['DuplicatesAllowed']))
            elif self.game_type == self.config["WAREHOUSE_LOGISTICS_GAME_TYPE_ID"]:
                self.game_styles_listbox.insert(index, self.config["WAREHOUSE_LOGISTICS_GAME_STYLE_LISTBOX_TEXT"].format(game_style['GameStyleId'],
                                                                                                                         game_style['Stake'],
                                                                                                                         game_style['GameTypeSpecificInfo']['WarehouseDimensions'][0],
                                                                                                                         game_style['GameTypeSpecificInfo']['WarehouseDimensions'][1]))
            elif self.game_type == self.config["FOUR_IN_A_ROW_GAME_TYPE_ID"]:
                self.game_styles_listbox.insert(index, self.config["FOUR_IN_A_ROW_GAME_STYLE_LISTBOX_TEXT"].format(game_style['GameStyleId'],
                                                                                                                   game_style['Stake'],
                                                                                                                   game_style['GameTypeSpecificInfo']['Dimensions'][0],
                                                                                                                   game_style['GameTypeSpecificInfo']['Dimensions'][1],
                                                                                                                   game_style['GameTypeSpecificInfo']['Connections']))
            elif self.game_type == self.config["WHO_IS_WHO_GAME_TYPE_ID"]:
                self.game_styles_listbox.insert(index, self.config["WHO_IS_WHO_GAME_STYLE_LISTBOX_TEXT"].format(game_style['GameStyleId'],
                                                                                                                game_style['Stake'],
                                                                                                                game_style['GameTypeSpecificInfo']['NumCharacters'],
                                                                                                                game_style['GameTypeSpecificInfo']['ComparisonRound']))
            elif self.game_type == self.config["REVERSING_STONES_GAME_TYPE_ID"]:
                self.game_styles_listbox.insert(index, self.config["REVERSING_STONES_GAME_STYLE_LISTBOX_TEXT"].format(game_style['GameStyleId'],
                                                                                                                      game_style['Stake'],
                                                                                                                      game_style['GameTypeSpecificInfo']['Dimensions'][0],
                                                                                                                      game_style['GameTypeSpecificInfo']['Dimensions'][1],
                                                                                                                      game_style['GameTypeSpecificInfo']['Holes'],
                                                                                                                      game_style['GameTypeSpecificInfo']['Timeout ms']))
            elif self.game_type == self.config["CHECKERS_GAME_TYPE_ID"]:
                self.game_styles_listbox.insert(index, self.config["CHECKERS_GAME_STYLE_LISTBOX_TEXT"].format(game_style['GameStyleId'],
                                                                                                              game_style['Stake'],
                                                                                                              game_style['GameTypeSpecificInfo']['Dimensions'][0],
                                                                                                              game_style['GameTypeSpecificInfo']['Dimensions'][1],
                                                                                                              game_style['GameTypeSpecificInfo']['Timeout ms']))
            elif self.game_type == self.config["GO_GAME_TYPE_ID"]:
                self.game_styles_listbox.insert(index, self.config["GO_GAME_STYLE_LISTBOX_TEXT"].format(game_style['GameStyleId'],
                                                                                                        game_style['Stake'],
                                                                                                        game_style['GameTypeSpecificInfo']['Dimensions'][0],
                                                                                                        game_style['GameTypeSpecificInfo']['Dimensions'][1],
                                                                                                        "CAPTURE" if game_style['GameTypeSpecificInfo']['IsCaptureGo'] else game_style['GameTypeSpecificInfo']['ScoringMethod'],
                                                                                                        game_style['GameTypeSpecificInfo']['Timeout ms']))
            elif self.game_type == self.config["LEXICO_GAME_TYPE_ID"]:
                self.game_styles_listbox.insert(index, self.config["LEXICO_GAME_STYLE_LISTBOX_TEXT"].format(game_style['GameStyleId'],
                                                                                                            game_style['Stake'],
                                                                                                            game_style['GameTypeSpecificInfo']['Dimensions'][0],
                                                                                                            game_style['GameTypeSpecificInfo']['Dimensions'][1],
                                                                                                            game_style['GameTypeSpecificInfo']['TileMultipliers'],
                                                                                                            game_style['GameTypeSpecificInfo']['Timeout ms']))
            elif self.game_type == self.config["DOMINOES_GAME_TYPE_ID"]:
                self.game_styles_listbox.insert(index, self.config["DOMINOES_GAME_STYLE_LISTBOX_TEXT"].format(game_style['GameStyleId'],
                                                                                                              game_style['Stake'],
                                                                                                              game_style['GameTypeSpecificInfo']['SpotNo'],
                                                                                                              game_style['GameTypeSpecificInfo']['Timeout ms']))
            else:
                raise ValueError('INVALID GAME TYPE PARAMETER')

            self.game_style_ids.append(game_style['GameStyleId'])
            # self.game_styles_listbox.select_set(GAME_STYLE_LISTBOX_DEFAULT_SELECTION)

    def reset_game_styles_listbox(self):
        """Clear the content of the game styles listbox."""

        if self.game_styles_listbox.size() != 0:
            self.game_styles_listbox.delete(0, 'end')

            self.game_style_ids = []

    def refresh_game_styles_clicked(self):
        """Click handler for the 'Refresh Game Styles' button."""

        res = self.get_list_of_game_styles()
        game_styles = res['GameStyles']
        self.set_game_styles_listbox(game_styles)

    def find_game_clicked(self):
        """Click handler for the 'Find Game' button"""

        self.find_game_button.config(state=DISABLED)
        self.cancel_stop_game_button.config(state=ENABLED)
        self.game_styles_listbox.unbind('<Double-1>')
        self.game_styles_listbox.unbind('<Return>')
        self.game_styles_listbox.config(state=DISABLED)
        self.clear_all_boards()

        # Here we dispatch the work to a separate thread, to keep the GUI responsive.
        if not MAC:
            threading.Thread(target=self.game_loop, daemon=True).start()
        else:
            self.game_loop()  # Doesn't work on MACs

    def find_game_double_clicked(self, _):
        self.find_game_clicked()

    def game_type_selected(self, _):
        self.game_type = self.config["COMBOBOX_INDEX"][self.gameTypeCmb.current()][1]
        res = self.get_list_of_game_styles()
        if res['Result'] == 'SUCCESS':
            game_styles = res['GameStyles']
            self.set_game_styles_listbox(game_styles)
            self.get_icon()
            self.player.destroy()
            self.opponent.destroy()
            self.create_visuals()

    def get_icon(self):
        try:
            if WINDOWS:
                self.master.iconbitmap("assets/{0}/icon.ico".format(self.game_type))
            else:
                self.master.iconbitmap("./assets/{0}/icon.xbm".format(self.game_type))
        except Exception as e:
            print(e)

    def create_visuals(self):
        if self.game_type == self.config["NULL_GAME_TYPE_ID"]:
            self.player = null_visuals.NullVisuals(self.middleFrameRight)  # Game Display Table
            self.opponent = null_visuals.NullVisuals(self.middleFrameRight)  # Game Display Table
        elif self.game_type == self.config["BATTLESHIPS_GAME_TYPE_ID"]:
            self.player = battleships_visuals.BattleshipsVisuals(self.middleFrameRight)  # Game Display Table
            self.opponent = battleships_visuals.BattleshipsVisuals(self.middleFrameRight)  # Game Display Table
        elif self.game_type == self.config["NOUGHTS_AND_CROSSES_GAME_TYPE_ID"]:
            self.player = noughts_and_crosses_visuals.NoughtsAndCrossesVisuals(self.middleFrameRight)  # Game Display Table
            self.opponent = noughts_and_crosses_visuals.NoughtsAndCrossesVisuals(self.middleFrameRight)  # Game Display Table
        elif self.game_type == self.config["TRAVELLING_SALESDRONE_GAME_TYPE_ID"]:
            self.player = travelling_salesdrone_visuals.TravellingSalesdroneVisuals(self.middleFrameRight)  # Game Display Table
            self.opponent = travelling_salesdrone_visuals.TravellingSalesdroneVisuals(self.middleFrameRight)  # Game Display Table
        elif self.game_type == self.config["PREDICTIVE_TEXT_GAME_TYPE_ID"]:
            self.player = predictive_text_visuals.PredictiveTextVisuals(self.middleFrameRight)  # Game Display Table
            self.opponent = predictive_text_visuals.PredictiveTextVisuals(self.middleFrameRight)  # Game Display Table
        elif self.game_type == self.config["TWIST_CUBE_GAME_TYPE_ID"]:
            self.player = twist_cube_visuals.TwistCubeVisuals(self.middleFrameRight)  # Game Display Table
            self.opponent = twist_cube_visuals.TwistCubeVisuals(self.middleFrameRight)  # Game Display Table
        elif self.game_type == self.config["SLIDING_PUZZLE_GAME_TYPE_ID"]:
            self.player = sliding_puzzle_visuals.SlidingPuzzleVisuals(self.middleFrameRight)  # Game Display Table
            self.opponent = sliding_puzzle_visuals.SlidingPuzzleVisuals(self.middleFrameRight)  # Game Display Table
        elif self.game_type == self.config["BLURRY_WORD_GAME_TYPE_ID"]:
            self.player = blurry_word_visuals.MicrosoftCognitiveChallengeVisuals(self.middleFrameRight)  # Game Display Table
            self.opponent = blurry_word_visuals.MicrosoftCognitiveChallengeVisuals(self.middleFrameRight)  # Game Display Table
        elif self.game_type == self.config["MASTERMIND_GAME_TYPE_ID"]:
            self.player = mastermind_visuals.MastermindVisuals(self.middleFrameRight)  # Game Display Table
            self.opponent = mastermind_visuals.MastermindVisuals(self.middleFrameRight)  # Game Display Table
        elif self.game_type == self.config["WAREHOUSE_LOGISTICS_GAME_TYPE_ID"]:
            self.player = warehouse_logistics_visuals.WarehouseLogisticsVisuals(self.middleFrameRight)  # Game Display Table
            self.opponent = warehouse_logistics_visuals.WarehouseLogisticsVisuals(self.middleFrameRight)  # Game Display Table
        elif self.game_type == self.config["FOUR_IN_A_ROW_GAME_TYPE_ID"]:
            self.player = four_in_a_row_visuals.FourInARowVisuals(self.middleFrameRight)  # Game Display Table
            self.opponent = four_in_a_row_visuals.FourInARowVisuals(self.middleFrameRight)  # Game Display Table
        elif self.game_type == self.config["WHO_IS_WHO_GAME_TYPE_ID"]:
            self.player = who_is_who_visuals.WhoIsWhoVisuals(self.middleFrameRight)  # Game Display Table
            self.opponent = who_is_who_visuals.WhoIsWhoVisuals(self.middleFrameRight)  # Game Display Table
        elif self.game_type == self.config["REVERSING_STONES_GAME_TYPE_ID"]:
            self.player = reversing_stones_visuals.ReversingStonesVisuals(self.middleFrameRight)  # Game Display Table
            self.opponent = reversing_stones_visuals.ReversingStonesVisuals(self.middleFrameRight)  # Game Display Table
        elif self.game_type == self.config["CHECKERS_GAME_TYPE_ID"]:
            self.player = checkers_visuals.CheckersVisuals(self.middleFrameRight)  # Game Display Table
            self.opponent = checkers_visuals.CheckersVisuals(self.middleFrameRight)  # Game Display Table
        elif self.game_type == self.config["GO_GAME_TYPE_ID"]:
            self.player = go_visuals.GoVisuals(self.middleFrameRight)  # Game Display Table
            self.opponent = go_visuals.GoVisuals(self.middleFrameRight)  # Game Display Table
        elif self.game_type == self.config["LEXICO_GAME_TYPE_ID"]:
            self.player = lexico_visuals.LexicoVisuals(self.middleFrameRight)  # Game Display Table
            self.opponent = lexico_visuals.LexicoVisuals(self.middleFrameRight)  # Game Display Table
        elif self.game_type == self.config["DOMINOES_GAME_TYPE_ID"]:
            self.player = dominoes_visuals.DominoesVisuals(self.middleFrameRight)  # Game Display Table
            self.opponent = dominoes_visuals.DominoesVisuals(self.middleFrameRight)  # Game Display Table
        else:
            raise ValueError('INVALID GAME TYPE PARAMETER')
        self.player.grid(row=1, column=3)
        self.opponent.grid(row=1, column=4)

    def game_loop(self):
        """Loop through finding and playing games."""

        while True:
            self.clear_all_boards()
            mover.persistentData = {}
            self.find_game()
            self.update_balance()
            if self.game_cancelled:
                break
            self.play_game()
            self.update_balance()
            if self.close_after_game:
                self.close_button.invoke()
            if self.game_cancelled:
                break
            if not self.play_again.get():
                break

        self.find_game_button.config(state=ENABLED)
        self.cancel_stop_game_button.config(state=DISABLED, text=CANCEL_GAME_TEXT)
        self.game_styles_listbox.bind('<Double-1>', self.find_game_double_clicked)
        self.game_styles_listbox.bind('<Return>', self.find_game_double_clicked)
        self.game_styles_listbox.config(state=ENABLED)
        self.game_cancelled = False

    def find_game(self):
        """Find a game."""

        offer_game_res = self.offer_game()

        if offer_game_res['Result'] == 'INVALID_LOGIN_OR_PASSWORD':
            self.cancel_stop_game_clicked()
            if 'ErrorMessage' in offer_game_res and offer_game_res['ErrorMessage'] == 'Check of OpponentId failed':
                self.resultText.config(text='Invalid Opponent ID')
            else:
                self.resultText.config(text='Invalid login or password')
        elif offer_game_res['Result'] == 'INSUFFICIENT_BALANCE':
            self.cancel_stop_game_clicked()
            self.resultText.config(text='Insufficient balance')
        elif offer_game_res['Result'] == 'BOT_IS_INACTIVE':
            self.cancel_stop_game_clicked()
            self.resultText.config(text='Bot is inactive')
        else:
            self.player_key = offer_game_res['PlayerKey']
            if offer_game_res['Result'] == 'WAITING_FOR_GAME':
                self.wait_for_game()

    def offer_game(self):
        """Offer a game."""

        self.cancel_game()  # Cancel the last outstanding game offer that was made

        opponent_id = self.specify_opponent_cmb.get()
        if len(opponent_id) == 0:
            opponent_id = None
        try:
            game_style_id = self.game_style_ids[int(self.game_styles_listbox.curselection()[0])]
        except IndexError:
            self.game_styles_listbox.select_set(GAME_STYLE_LISTBOX_DEFAULT_SELECTION)
            game_style_id = self.game_style_ids[0]

        req = {'BotId': self.bot_id,
               'BotPassword': self.bot_password,
               'MaximumWaitTime': 1000,
               'GameStyleId': game_style_id,
               'DontPlayAgainstSameUser': self.do_not_play_same_user.get(),
               'DontPlayAgainstSameBot': False,
               'OpponentId': opponent_id}
        url = self.config["BASE_URL"] + self.config["OFFER_GAME_EXTENSION"]

        return DemoClient.make_api_call(url, req)

    def wait_for_game(self):
        """Wait for game to start."""
        self.resultText.config(text='Waiting for game')
        while True:
            if self.game_cancelled:
                self.cancel_game()
                self.find_game_button.config(state=ENABLED)
                self.cancel_stop_game_button.config(state=DISABLED, text=CANCEL_GAME_TEXT)
                self.game_styles_listbox.bind('<Double-1>', self.find_game_double_clicked)
                self.game_styles_listbox.bind('<Return>', self.find_game_double_clicked)
                self.game_styles_listbox.config(state=ENABLED)
                break
            poll_results = self.poll_for_game_state()

            if poll_results['Result'] == 'SUCCESS':
                break
            if poll_results['Result'] == 'INVALID_PLAYER_KEY' or poll_results['Result'] == 'GAME_HAS_ENDED' or poll_results['Result'] == 'GAME_WAS_STOPPED':
                self.game_cancelled = True
            time.sleep(2)

    def play_game(self):
        """Play a game."""
        self.resultText.config(text='Playing game')
        self.in_game = True

        poll_results = self.poll_for_game_state()

        if poll_results["Result"] != "SUCCESS":
            return

        game_state = poll_results['GameState']

        title = format('Game ID: ' + str(game_state['GameId']))
        title += format(' / Style: ' + str(self.game_style_ids[int(self.game_styles_listbox.curselection()[0])]))
        title += "\n"
        versus = format(self.bot_id + ' vs ' + game_state['OpponentId'])

        self.clear_game_title_text()
        self.set_game_title_text(title, "")
        self.set_game_title_text(versus, "bold")

        self.middleFrame.update()

        while True:
            if self.game_cancelled:
                break

            if game_state['IsMover']:
                self.resultText.config(text='Playing Game - Your Turn')
                move = mover.calculate_move(self.game_type, game_state)
                move_results = self.make_move(move)

                if move_results['Result'] == 'INVALID_MOVE':
                    self.resultText.config(text="Invalid Move")
                elif move_results['Result'] != 'SUCCESS':
                    self.resultText.config(text='Game has ended: ' + move_results['Result'])
                    print(str(move_results))
                    print("Game ended")
                    break
                else:
                    game_state = move_results['GameState']
            else:
                self.resultText.config(text="Playing Game - Opponent's Turn")

                # ---- Code here will be called on your opponent's turn ----

                # ----------------------------------------------------------

                poll_results = self.poll_for_game_state()

                if poll_results['Result'] != 'SUCCESS':
                    self.resultText.config(text='Game has ended: ' + poll_results['Result'])
                    break
                game_state = poll_results['GameState']

            if game_state['GameStatus'] != 'RUNNING':
                break

            self.middleFrameRight.update()

            try:
                if int(self.thinking_time_entry.get()) > 0:
                    time.sleep((int(self.thinking_time_entry.get()) / 1000))
                else:
                    time.sleep(0.1)
            except ValueError:
                time.sleep(0.1)

        self.set_in_game(False)

    def make_move(self, move):
        """Make a move."""

        req = {'BotId': self.bot_id,
               'BotPassword': self.bot_password,
               'PlayerKey': self.player_key,
               'Move': move}
        url = self.config["BASE_URL"] + self.config["MAKE_MOVE_EXTENSION"]

        result = DemoClient.make_api_call(url, req)

        if result['Result'] == 'SUCCESS' or "GAME_HAS_ENDED" in result['Result']:
            print(result)
            try:
                self.player.draw_game_state(result['GameState'], True)
                self.opponent.draw_game_state(result['GameState'], False)
            except Exception as e:
                print("Gamestate error: " + str(e))

        return result

    def poll_for_game_state(self):
        """Poll the server for the latest GameState."""

        req = {'BotId': self.bot_id,
               'BotPassword': self.bot_password,
               'MaximumWaitTime': 1000,
               'PlayerKey': self.player_key}
        url = self.config["BASE_URL"] + self.config["POLL_FOR_GAME_STATE_EXTENSION"]

        result = DemoClient.make_api_call(url, req)
        if result['Result'] == 'SUCCESS' or "GAME_HAS_ENDED" in result['Result']:
            self.player.draw_game_state(result['GameState'], True)
            self.opponent.draw_game_state(result['GameState'], False)

        return result

    def cancel_stop_game_clicked(self):
        self.game_cancelled = True
        self.cancel_game()
        self.find_game_button.config(state=ENABLED)
        self.cancel_stop_game_button.config(state=DISABLED, text=CANCEL_GAME_TEXT)
        self.game_styles_listbox.bind('<Double-1>', self.find_game_double_clicked)
        self.game_styles_listbox.bind('<Return>', self.find_game_double_clicked)
        self.game_styles_listbox.config(state=ENABLED)

    def cancel_game(self):
        print("Cancelling last game offer")
        if self.player_key is None:
            return
        req = {'BotId': self.bot_id,
               'BotPassword': self.bot_password,
               'PlayerKey': self.player_key}

        url = self.config["BASE_URL"] + self.config["CANCEL_GAME_OFFER_EXTENSION"]
        DemoClient.make_api_call(url, req)
        try:
            self.resultText.config(text='Cancelled game')
        except Exception as e:
            print(str(e) + " -- Demo client has been closed")

    def update_balance(self):
        res = self.get_list_of_game_styles()
        self.set_balance(res['Balance'])

    @staticmethod
    def make_api_call(url, req):
        """Make an API call."""
        while True:
            try:
                res = requests.post(url, json=req, headers=API_CALL_HEADERS, timeout=60.0)
                try:
                    jres = res.json()
                    if 'Result' in jres:
                        return jres
                    time.sleep(0.1)
                except ValueError:
                    time.sleep(0.1)
            except requests.ConnectionError:
                time.sleep(0.1)
            except requests.Timeout:
                time.sleep(0.1)
            except requests.HTTPError:
                time.sleep(0.1)
            except BaseException as e:  # Bad code but needed for testing purposes
                print(e)
                time.sleep(0.1)


def int_with_commas(x):
    if type(x) not in [type(0), type(0)]:
        raise TypeError("Parameter must be an integer.")
    if x < 0:
        return '-' + int_with_commas(-x)
    result = ''
    while x >= 1000:
        x, r = divmod(x, 1000)
        result = ",%03d%s" % (r, result)
    return "%d%s" % (x, result)


parser = argparse.ArgumentParser(description='Set optional running parameters')
parser.add_argument('--botid', default=None, help='log in with this bot name')
parser.add_argument('--password', default=None, help='log in with this password')
parser.add_argument('--gametype', default=None, help='play this gametype')
parser.add_argument('--gamestyle', default=None, help='play this gamestyle')
parser.add_argument('--timeout', default=0, help='have this timeout in milliseconds')
parser.add_argument('--playanothergame', action='store_true', help='Play another game when complete')
parser.add_argument('--dontplaysameuserbot', action='store_true', help='Don\'t play another user in the same account')
parser.add_argument('--closeaftergame', action='store_true', help='Close the client once the game has completed (takes priority over playanothergame)')
cmd_args = parser.parse_args()
root = Tk()
my_gui = DemoClient(root, cmd_args)
root.mainloop()
