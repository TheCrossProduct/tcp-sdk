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

    if not entries:
        return entries

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
    from datetime import datetime

    if not entries:
        return entries

    if att not in entries[0]:
        return entries

    if is_datetime_format(entries[0][att]):
        return sorted (entries, key=lambda x: datetime.fromisoformat(x[att]), reverse=True)

    return sorted (entries, key=lambda x: x[att], reverse=True) 

class TableFromDB:

    def __init__ (self, endpoint, model, plural, ignores, sorting_att, width, height):

        self.endpoint = endpoint
        self.model = model
        self.plural = plural
        self.ignores = ignores
        self.sorting_att = sorting_att
        self.width = width
        self.height = height

        self.entries = None

    def load (self):
        from . import exceptions

        try:
            self.entries = self.endpoint.get ()[self.plural]
        except (exceptions.HttpClientError, exceptions.HttpServerError) as err:
            with open (f"log-dashboard.txt", 'a') as f:
                f.write (f"TableFrom{self.model}: {err.content}")

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
        table.max_table_width = table.min_table_width = self.width -1
        table.max_table_height = table.min_table_height = self.height -1 
        table.field_names = self.entries[0].keys ()
        table.add_rows ([x.values() for x in self.entries])

        out = table.get_string ().split('\n')

        return out

class TableData:

    def __init__ (self, endpoint):

        self.endpoint = endpoint
        self.model = 'Data'
        self.entries = None

    def load (self):
        from . import exceptions

        try:
            self.entries = self.endpoint.get ()
        except (exceptions.HttpClientError, exceptions.HttpServerError) as err:
            with open (f"log-dashboard.txt", 'a') as f:
                f.write (f"TableData: {err.content}")

        if not self.entries:
            return [f"No {self.model}"]

        return self.display ()

    def display (self):

        all_files = []

        for prefix in self.entries:
            if prefix != "files":
                all_files += [f'{prefix}@{x}' for x in self.entries[prefix]]
            else:
                all_files += self.entries[prefix]

        out = [f'| {x}' for x in all_files]

        return out

def update_tables (refresh_delay, text_queue, arg_queue, stop_updating, client, width, height):

    import time
    from datetime import datetime

    models = [(client.query().app.list("Process"), "Process", "processes"), 
              (client.query().app.list("Instance"),"Instance", "instances"), 
              (client.query().app.list("Remote"),  "Remote", "remotes"),
              (client.query().lics,                "License", "licenses")]

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

    tables = { name: TableFromDB (endpoint, name, plural, ignores[name], sorting_atts[name], width, height) for endpoint, name, plural in models }
    tables['Data'] = TableData (client.query().data)

    if refresh_delay == 0:
        updated_text = {}
        for model in tables:
            tables[model].width, tables[model].height = width, height
            updated_text[model] = tables[model].load()
        text_queue.put ( updated_text )
        return

    while True:

        if arg_queue.qsize() > 0:

            new_args = arg_queue.get ()

            width = new_args['width']
            height = new_args['height']

            for model in tables:
                tables[model].width, tables[model].height = width, height

        updated_text = {}
        for model in tables:
            updated_text[model] = tables[model].load()

        text_queue.put ( updated_text )

        if stop_updating.wait (refresh_delay):
           break 

def update_position (text, model, height, pos_table_screen, pos_cursor_screen, pos_cursor_table, offset):

    # TECHDEBT: This should not work for abs(offset) > 1

    pos_of_plus = []

    for ii, line in enumerate(text):
        if line.startswith('|'):
            pos_of_plus.append (ii)

    if not pos_of_plus:
        return 0, 0, 0

    # First update pos_cursor_table: 
    #   - pin to closest plus
    for ii, pos in enumerate(pos_of_plus):
        if pos > pos_cursor_table:
            break

    new_pos_cursor_table = pos_of_plus[min(max(0, (ii-1)+offset), len(pos_of_plus)-1)]
    diff = new_pos_cursor_table - pos_cursor_table
    pos_cursor_table = new_pos_cursor_table

    # Then update table on screen:
    if pos_cursor_screen + diff < 0:
        pos_table_screen = max(0,pos_table_screen+diff)
    if pos_cursor_screen + diff > height:
        pos_table_screen = min(pos_table_screen+diff, len(text)-height) 

    # finally update cursor
    pos_cursor_screen = min(max(0, pos_cursor_screen + diff), height) 

    return pos_table_screen, pos_cursor_screen, pos_cursor_table


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

    pos_cursor_screen = { model:0 for model in text.keys() }
    pos_table_screen = { model:0 for model in text.keys() }
    pos_cursor_table = { model:0 for model in text.keys() } 

    dims = [80, 80]
    ch = ''

    offset_screen_x, offset_screen_y = 1, 1
    substract_to_screen_x, substract_to_screen_y = 0,5
    screen_width = dims[1] - offset_screen_x - substract_to_screen_x
    screen_height = dims[0] - offset_screen_y - substract_to_screen_y

    text_queue = queue.Queue()
    text_queue.put (text)

    arg_queue = queue.Queue()
    arg_queue.put({'width':  screen_width, 
                   'height': screen_height})

    stop_updating = threading.Event ()

    th = threading.Thread (
            target=update_tables, 
            args=(refresh_delay, 
                  text_queue, 
                  arg_queue,
                  stop_updating, 
                  client, 
                  dims[1], 
                  dims[0]))

    th.start ()

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

        while not should_exit:

            queried_dims = stdscr.getmaxyx()

            if queried_dims[0] != dims[0] or queried_dims[1] != dims[1]:

                dims = queried_dims
                screen_width = dims[1] - offset_screen_x - substract_to_screen_x
                screen_height = dims[0] - offset_screen_y - substract_to_screen_y

                arg_queue.put({'width':  screen_width, 
                               'height': screen_height})

                # Manually calls update_tables
                update_tables (0, 
                               text_queue,
                               arg_queue,
                               stop_updating,
                               client,
                               screen_width,
                               screen_height)

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

            for ll, line in enumerate(text[current][pos_table_screen[current]:min(len(text[current]), pos_table_screen[current] + screen_height)]):
                stdscr.addstr(offset_screen_y+ll, offset_screen_x, line, curses.color_pair(0))

            stdscr.addstr(dims[0]-1, 0, ' '*(dims[1]-1), curses.color_pair(1))
            stdscr.addstr(dims[0]-1, 0, footnote, curses.color_pair(1))

            stdscr.addstr (pos_cursor_screen[current]+offset_screen_y, 0, '>', curses.color_pair(2))

            stdscr.refresh ()

            try:
                ch = stdscr.getch ()
            except:
                pass                 

            if ch == curses.KEY_LEFT:

                index_current = list(text.keys()).index(current)
                index_current = max(0, index_current-1)
                current = list(text.keys())[index_current]

            elif ch == curses.KEY_RIGHT:

                index_current = list(text.keys()).index(current)
                index_current = min (len(text)-1, index_current+1)
                current = list(text.keys())[index_current]

            elif ch == curses.KEY_UP:

                pos_table_screen[current], pos_cursor_screen[current], pos_cursor_table[current] = update_position (text[current], current, screen_height, pos_table_screen[current], pos_cursor_screen[current], pos_cursor_table[current], -1)

            elif ch == curses.KEY_DOWN:

                pos_table_screen[current], pos_cursor_screen[current], pos_cursor_table[current] = update_position (text[current], current, screen_height, pos_table_screen[current], pos_cursor_screen[current], pos_cursor_table[current], 1)

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

