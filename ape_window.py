import tkinter as tk
import tkinter.filedialog as fdialog
import tkinter.ttk as ttk
import tkinter.messagebox as msgb
import os
from readers.read_blast import BlastReader
from read_muse_embeds import load_embeddings, closest_words


class PostEditWindow(object):

    def __init__(self, application):
        self.app = application
        self.blast_window = tk.Toplevel(application.master)
        self.blast_widget = tk.Frame(self.blast_window)
        self.blast_widget.grid(row=0, column=0, pady=10, padx=10)

        # BLAST
        self.blast_path_label = tk.Label(self.blast_widget, text='BLAST file')
        self.blast_path_label.grid(row=0, column=0, sticky=tk.W)
        self.blast_path_text = tk.Text(self.blast_widget, height=1)
        self.blast_path_text.config(state=tk.DISABLED)
        self.blast_path_text.grid(row=0, column=1, padx=10)
        self.blast_path_button = tk.Button(self.blast_widget, text='Select')
        self.blast_path_button.bind('<Button-1>', self.get_filename_callback)
        self.blast_path_button.message = 'BLAST'
        self.blast_path_button.grid(row=0, column=2)

        # EN
        self.en_path_label = tk.Label(self.blast_widget, text='Embeddings EN')
        self.en_path_label.grid(row=1, column=0, sticky=tk.W)
        self.en_path_text = tk.Text(self.blast_widget, height=1)
        self.en_path_text.config(state=tk.DISABLED)
        self.en_path_text.grid(row=1, column=1, padx=10)
        self.en_path_button = tk.Button(self.blast_widget, text='Select')
        self.en_path_button.bind('<Button-1>', self.get_filename_callback)
        self.en_path_button.message = 'EN'
        self.en_path_button.grid(row=1, column=2)

        # PT
        self.pt_path_label = tk.Label(self.blast_widget, text='Embeddings PT')
        self.pt_path_label.grid(row=2, column=0, sticky=tk.W)
        self.pt_path_text = tk.Text(self.blast_widget, height=1)
        self.pt_path_text.config(state=tk.DISABLED)
        self.pt_path_text.grid(row=2, column=1, padx=10)
        self.pt_path_button = tk.Button(self.blast_widget, text='Select')
        self.pt_path_button.bind('<Button-1>', self.get_filename_callback)
        self.pt_path_button.message = 'PT'
        self.pt_path_button.grid(row=2, column=2)

        self.error_type = tk.StringVar(self.blast_widget)
        self.error_type.set(application.errors[0])

        self.error_label = tk.Label(self.blast_widget, text='Error type')
        self.error_label.grid(row=3, column=0, pady=10)
        self.error_menu = tk.OptionMenu(
            self.blast_widget, self.error_type, *application.errors)
        self.error_menu.grid(row=3, column=1, columnspan=2,
                             pady=10, sticky=tk.W)

        # Concluido
        self.done_button = tk.Button(
            self.blast_widget, text='Done', command=lambda: self.load_blast())
        self.done_button.grid(row=4, column=0, columnspan=2, pady=10)
        self.cancel_button = tk.Button(
            self.blast_widget, text='Cancel', command=self.close_window_callback)
        self.cancel_button.grid(row=4, column=1, columnspan=3, pady=10)

    def get_filename_callback(self, event):
        filename = fdialog.askopenfile(title='Select a file')
        try:
            assert filename
        except AssertionError:
            pass
        else:
            if event.widget.message == 'BLAST':
                self.blast_path_text.config(state=tk.NORMAL)
                self.blast_path_text.delete('1.0', tk.END)
                self.blast_path_text.insert('end', filename.name)
                self.blast_path_text.config(state=tk.DISABLED)
            elif event.widget.message == 'EN':
                self.en_path_text.config(state=tk.NORMAL)
                self.en_path_text.delete('1.0', tk.END)
                self.en_path_text.insert('end', filename.name)
                self.en_path_text.config(state=tk.DISABLED)
            else:
                self.pt_path_text.config(state=tk.NORMAL)
                self.pt_path_text.delete('1.0', tk.END)
                self.pt_path_text.insert('end', filename.name)
                self.pt_path_text.config(state=tk.DISABLED)
    
    def close_window_callback(self):
        self.blast_window.destroy()

    def load_blast(self):
        blast_path = self.blast_path_text.get('1.0', tk.END).strip()
        en_path = self.en_path_text.get('1.0', tk.END).strip()
        pt_path = self.pt_path_text.get('1.0', tk.END).strip()
        try:
            assert blast_path
            assert en_path
            assert pt_path
        except AssertionError:
            tk.messagebox.showerror(
                'Select files', 'It is necessary to selct all files.')
        else:
            try:
                blast_reader = BlastReader(blast_path)
            except FileNotFoundError:
                tk.messagebox.showerror(
                    'File not found', 'BLAST file not found.')
            else:
                errors = blast_reader.get_filtered_errors(
                    [self.error_type.get()])
                emb_en, emb_pt = load_embeddings(en_path, pt_path)

                self.filename = os.path.splitext(
                    os.path.split(blast_path)[1])[0] + '_APE_' + self.error_type.get()
                save_file = open(self.filename, 'w')
                save_file.write('@annotations\n')
                save_file.write(str(self.app.cur_line))
                save_file.write('\n')

                # Progresso
                error_num = 0
                progress_var = tk.DoubleVar()
                progress_bar = ttk.Progressbar(
                    self.blast_window, variable=progress_var, maximum=len(errors))
                self.done_button.destroy()
                self.cancel_button.grid(row=5, column=0, columnspan=3, pady=10)
                progress_bar.grid(row=4, column=0, columnspan=3, pady=10)

                for error in errors:
                    progress_var.set(error_num)
                    line = error[0]
                    save_file.write(' '.join(blast_reader.src_lines[line]))
                    save_file.write('\n')
                    save_file.write(' '.join(blast_reader.ref_lines[line]))
                    save_file.write('\n')
                    save_file.write(' '.join(blast_reader.sys_lines[line]))
                    save_file.write('\n')

                    error_info = [','.join(map(str, e)) for e in error[1][:-1]]
                    error_info.append(error[1][-1])
                    save_file.write('#'.join(error_info))
                    save_file.write('\n')

                    sentence_to_correct = blast_reader.src_lines[line]
                    sys_sentence = blast_reader.sys_lines[line]
                    candidates = list()
                    for i in error[1][0]:
                        if i > 0:
                            candidates.extend(['-.-'.join([w[0], 'white']) for w in closest_words(
                                sentence_to_correct[i], emb_en, emb_pt,
                                words_to_ignore=[sys_sentence[j] for j in error[1][1]])])
                        else:
                            candidates.append('-.-'.join(['***', 'white']))
                    save_file.write('#@'.join(candidates))
                    save_file.write('\n')
                    self.blast_window.update_idletasks()
                    error_num = error_num + 1

                save_file.close()
                msgb.showinfo('Saved', 'File saved as: ' + self.filename)
                self.close_window_callback()