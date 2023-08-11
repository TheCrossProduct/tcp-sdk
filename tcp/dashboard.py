def is_datetime_format (val):
    from datetime import datetime

    if not isinstance(val, str):
        return False
    try:
        datetime.fromisoformat (val)
    except ValueError:
        return False 
    return True

def prettier_fields (entries, model):
    ''' Some hacks to get prettier tables '''

    from datetime import datetime   

    out = entries

    if model == "License":
        for ii, lic in enumerate(entries):
            if " all" in lic["scope"]:
                out[ii]["scope"] = "all"

    for ii, ee in enumerate(entries):
        for field in ee:
            if isinstance (ee[field], float):
                entries[ii][field] = "%.2f" % ee[field]
            
            if is_datetime_format(ee[field]):
                # Truncating datetime to a more compact form
                entries[ii][field] = datetime.fromisoformat(ee[field]).isoformat(timespec='minutes')

    return out 

def sort_by_att (entries, att):

    if not entries:
        return entries

    if att not in entries[0]:
        return entries

    if is_datetime_format(entries[0][att]):
        return entries.sort (key=lambda x: datetime.fromisoformat(x), reverse=True)

    return entries.sort (key=lambda x: x[att], reverse=True) 

class TableFromDB:

    def __init__ (self, endpoint, model, ignores, sorting_att, width, height):

        self.endpoint = endpoint
        self.model = model
        self.ignores = ignores
        self.sorting_att = sorting_att
        self.width = width
        self.height = height

        self.entries = None

    def load (self):

        self.entries = self.endpoint.get ()

        if not self.entries:
            return [f"No {self.model}"]

        filtered = [{key: entry[key] for key in entry if key not in self.ignores} for entry in self.entries]
        prettier = prettier_fields (sort_by_att(filtered, self.sorting_att), self.model)

        self.entries = prettier

        return self.display ()

    def display (self):
        import prettytable

        if not self.entries:
            return [f"No {self.model}"]

        table = prettytable.PrettyTable()
#        table.max_table_width = table.min_table_width = width 
#        table.max_table_height = table.min_table_height = height 
        table.field_names = self.entries[0].keys ()
        table.add_rows ([x.values() for x in self.entries])

        out = table.get_string ().split('\n')
        return out

def update_tables (refresh_delay, text_queue, stop_updating, client, width, height):

    import time

    models = [(client.query().app.list("Process"), "Process"), 
              (client.query().app.list("Instance"),"Instance"), 
              (client.query().app.list("Remote"),  "Remote"),
              (client.query().lics,                "License")]

    ignores = {'Process':['user_id', 'endpoint', 'terminated', 'expires'],
               'Remote':['user_id', 'usr', 'input_path', 'output_path', 'working_path'],
               'Instance':['user_id', 'expires', 'ip', 'ssh_usr', 'input_path', 'working_path', 'output_path', 'num_cores', 'mem_required', 'ram_required'],
               'License':['user_id', 'created', 'last_failed', 'active']
              }
    
    sorting_atts = {
        'Process': 'launched',
        'Instance': 'launched',
        'Remote': 'instanciated',
        'License': 'created'
            }

    tables = [ TableFromDB (endpoint, name, ignores[name], sorting_atts[name], width, height) for endpoint, name in models ]

    while True:

        updated_text = { table.model: table.load()  for table in tables}

        updated_text['Data'] = ["No Data"]

        text_queue.put ( updated_text )

        if stop_updating.is_set ():
           break 

        time.sleep (refresh_delay)

def dashboard (client, refresh_delay):
    import curses
    import traceback
    import threading, queue

    text = { "Process": ["No Process"],
             "Instance": ["No Instance"],
             "Remote": ["No Remote"],
             "License": ["No License"],
             "Data": ["No Data"]}

    current = "Process"
    current_line = 0

    text_queue = queue.Queue()
    text_queue.put (text)

    dims = [80, 80]

    stop_updating = threading.Event ()

    th = threading.Thread (
            target=update_tables, 
            args=(refresh_delay, 
                  text_queue, 
                  stop_updating, 
                  client, 
                  dims[1], 
                  dims[0]-5))

    th.start ()

    ch = ''


    try:
        stdscr = curses.initscr()
        curses.noecho ()
        curses.cbreak ()
        curses.halfdelay(10*refresh_delay)
        stdscr.keypad(1)

        curses.start_color ()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_WHITE)

        should_exit = False

        current_pos = 0

        while not should_exit:

            dims = stdscr.getmaxyx()

            stdscr.clear ()

            if dims[0] < 40 and dims[1] < 40:
                stdscr.addstr (0, 0, "screen should be at least 40x40...")
                continue

            stdscr.addstr (0,0, ' '*dims[1], curses.color_pair(1))
            section_x_offset = 0
            for section in text.keys():
                headline = f" > {section}"

                if section == current:
                    stdscr.addstr (0, section_x_offset, headline, curses.color_pair(2))                    
                else:
                    stdscr.addstr (0, section_x_offset, headline, curses.color_pair(1))                    

                section_x_offset += len(headline)

            footnote = 'Press q to quit. Press up and down arrow to scroll. Press left and right to select which table.'

            if text_queue.qsize() > 0:
                text = text_queue.get ()

            stdscr.addstr(1, 0, '\n'.join(text[current][current_line:min(len(text[current]), dims[0]-5)]), curses.color_pair(0))

            stdscr.addstr(dims[0]-1, 0, ' '*(dims[1]-1), curses.color_pair(1))
            stdscr.addstr(dims[0]-1, 0, footnote, curses.color_pair(1))

            stdscr.refresh ()

            try:
                ch = stdscr.getch ()
            except:
                pass                 

            if ch == curses.KEY_LEFT:
                index_current = list(text.keys()).index(current)
                index_current = max(0, index_current-1)
                current = list(text.keys())[index_current]
                current_line = 0
            elif ch == curses.KEY_RIGHT:
                index_current = list(text.keys()).index(current)
                index_current = min (len(text)-1, index_current+1)
                current = list(text.keys())[index_current]
                current_line = 0
            elif ch == curses.KEY_UP:
                current_line = max(0, current_line-1)
            elif ch == curses.KEY_DOWN:
                current_line = min(max(0,(len(text[current])-dims[0]+5)), current_line+1)
            elif ch == ord('q'):
                should_exit = True

            curses.flushinp()

        stdscr.clear ()
        stdscr.addstr ("Exiting...")
        stdscr.refresh ()

    finally:

        stop_updating.set ()
        th.join()

        stdscr.keypad(0)
        curses.echo(); curses.nocbreak()
        curses.endwin()
        traceback.print_exc()

