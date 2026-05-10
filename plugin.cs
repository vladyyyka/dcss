using System;
using System.Collections.Generic;
using System.Drawing;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using MissionPlanner;
using MissionPlanner.Plugin;
using Newtonsoft.Json;

namespace DroneTrainingUI
{
    public class DroneTrainingUI : Plugin
    {
        public override string Name { get { return "DCSS Тренажер"; } }
        public override string Version { get { return "7.1-stable-details"; } }
        public override string Author { get { return "БВС Инструктор"; } }

        private MissionsForm missionsForm;
        private Timer initTimer;

        public override bool Init()
        {
            return true;
        }

        public override bool Loaded()
        {
            try
            {
                initTimer = new Timer();
                initTimer.Interval = 1000;
                initTimer.Tick += delegate
                {
                    initTimer.Stop();
                    AddMenuButton();
                };
                initTimer.Start();
                return true;
            }
            catch (Exception ex)
            {
                MessageBox.Show("Ошибка загрузки плагина: " + ex.Message, "DCSS", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return false;
            }
        }

        private void AddMenuButton()
        {
            if (MainV2.instance == null || MainV2.instance.MainMenu == null)
            {
                Timer retryTimer = new Timer();
                retryTimer.Interval = 1000;
                retryTimer.Tick += delegate
                {
                    retryTimer.Stop();
                    AddMenuButton();
                };
                retryTimer.Start();
                return;
            }

            MainV2.instance.BeginInvoke((MethodInvoker)delegate
            {
                ToolStripButton button = new ToolStripButton();
                button.Text = "DCSS Тренажер";
                button.DisplayStyle = ToolStripItemDisplayStyle.Text;
                button.Font = new Font("Segoe UI", 9, FontStyle.Bold);
                button.BackColor = Color.FromArgb(37, 99, 235);
                button.ForeColor = Color.White;
                button.Padding = new Padding(10, 2, 10, 2);
                button.Click += delegate { ShowMissionsForm(); };

                int index = Math.Max(0, MainV2.instance.MainMenu.Items.Count - 2);
                MainV2.instance.MainMenu.Items.Insert(index, button);
            });
        }

        private void ShowMissionsForm()
        {
            MainV2.instance.BeginInvoke((MethodInvoker)delegate
            {
                if (missionsForm == null || missionsForm.IsDisposed)
                {
                    missionsForm = new MissionsForm();
                }

                missionsForm.Show();
                missionsForm.BringToFront();
            });
        }

        public override bool Exit()
        {
            if (initTimer != null)
            {
                initTimer.Stop();
            }

            if (missionsForm != null && !missionsForm.IsDisposed)
            {
                missionsForm.Close();
            }

            return true;
        }
    }

    public class MissionsForm : Form
    {
        private DcssApiClient api;

        private TextBox txtServer;
        private TextBox txtLogin;
        private TextBox txtPassword;
        private Button btnLogin;
        private Button btnRefresh;
        private FlowLayoutPanel missionsPanel;
        private Label lblStatus;
        private Label lblUser;

        private readonly Dictionary<int, string> runningQuestGuids = new Dictionary<int, string>();
        private readonly Dictionary<int, Label> statusLabels = new Dictionary<int, Label>();

        private readonly Color Bg = Color.FromArgb(245, 247, 251);
        private readonly Color Card = Color.White;
        private readonly Color TextColor = Color.FromArgb(20, 30, 45);
        private readonly Color Muted = Color.FromArgb(90, 105, 125);
        private readonly Color Blue = Color.FromArgb(37, 99, 235);
        private readonly Color Green = Color.FromArgb(16, 185, 129);
        private readonly Color Orange = Color.FromArgb(249, 115, 22);
        private readonly Color Red = Color.FromArgb(220, 38, 38);

        public MissionsForm()
        {
            Text = "DCSS — Тренажер пилотирования";
            Width = 1100;
            Height = 760;
            MinimumSize = new Size(980, 650);
            StartPosition = FormStartPosition.CenterScreen;
            BackColor = Bg;
            ForeColor = TextColor;
            Font = new Font("Segoe UI", 9F, FontStyle.Regular);

            BuildUi();
        }

        private void BuildUi()
        {
            Controls.Clear();

            Panel header = new Panel();
            header.Dock = DockStyle.Top;
            header.Height = 82;
            header.BackColor = Color.White;
            header.Padding = new Padding(24, 12, 24, 8);
            Controls.Add(header);

            Label title = new Label();
            title.Text = "DCSS Тренажер пилотирования";
            title.Font = new Font("Segoe UI", 20F, FontStyle.Bold);
            title.ForeColor = TextColor;
            title.AutoSize = true;
            title.Location = new Point(24, 14);
            header.Controls.Add(title);

            Label subtitle = new Label();
            subtitle.Text = "Mission Planner + backend DCSS";
            subtitle.Font = new Font("Segoe UI", 9F, FontStyle.Regular);
            subtitle.ForeColor = Muted;
            subtitle.AutoSize = true;
            subtitle.Location = new Point(26, 52);
            header.Controls.Add(subtitle);

            lblUser = new Label();
            lblUser.Text = "Не авторизован";
            lblUser.Font = new Font("Segoe UI", 9F, FontStyle.Bold);
            lblUser.ForeColor = Muted;
            lblUser.AutoSize = true;
            header.Controls.Add(lblUser);
            header.Resize += delegate { lblUser.Location = new Point(header.Width - lblUser.Width - 24, 30); };
            lblUser.Location = new Point(header.Width - lblUser.Width - 24, 30);

            Panel loginPanel = new Panel();
            loginPanel.Dock = DockStyle.Top;
            loginPanel.Height = 88;
            loginPanel.BackColor = Bg;
            loginPanel.Padding = new Padding(24, 14, 24, 10);
            Controls.Add(loginPanel);
            loginPanel.BringToFront();

            Panel loginCard = new Panel();
            loginCard.Dock = DockStyle.Fill;
            loginCard.BackColor = Color.White;
            loginCard.BorderStyle = BorderStyle.FixedSingle;
            loginPanel.Controls.Add(loginCard);

            Label l1 = SmallLabel("Backend URL", 16, 8);
            Label l2 = SmallLabel("Логин", 310, 8);
            Label l3 = SmallLabel("Пароль", 490, 8);
            loginCard.Controls.Add(l1);
            loginCard.Controls.Add(l2);
            loginCard.Controls.Add(l3);

            txtServer = Input("http://127.0.0.1:8000", 16, 32, 270);
            txtLogin = Input("", 310, 32, 160);
            txtPassword = Input("", 490, 32, 160);
            txtPassword.PasswordChar = '*';

            btnLogin = NormalButton("Войти", 680, 30, 110, Blue, Color.White);
            btnLogin.Click += async delegate { await LoginAsync(); };

            btnRefresh = NormalButton("Обновить задания", 805, 30, 160, Color.FromArgb(235, 240, 247), TextColor);
            btnRefresh.Enabled = false;
            btnRefresh.Click += async delegate { await LoadMissionsAsync(); };

            loginCard.Controls.Add(txtServer);
            loginCard.Controls.Add(txtLogin);
            loginCard.Controls.Add(txtPassword);
            loginCard.Controls.Add(btnLogin);
            loginCard.Controls.Add(btnRefresh);

            Panel bottom = new Panel();
            bottom.Dock = DockStyle.Bottom;
            bottom.Height = 34;
            bottom.BackColor = Color.White;
            Controls.Add(bottom);

            lblStatus = new Label();
            lblStatus.Text = "Готов к работе. Выполните вход в backend DCSS.";
            lblStatus.ForeColor = Muted;
            lblStatus.Font = new Font("Segoe UI", 9F, FontStyle.Regular);
            lblStatus.AutoSize = true;
            lblStatus.Location = new Point(24, 9);
            bottom.Controls.Add(lblStatus);

            missionsPanel = new FlowLayoutPanel();
            missionsPanel.Dock = DockStyle.Fill;
            missionsPanel.FlowDirection = FlowDirection.TopDown;
            missionsPanel.WrapContents = false;
            missionsPanel.AutoScroll = true;
            missionsPanel.BackColor = Bg;
            missionsPanel.Padding = new Padding(24, 18, 24, 18);
            Controls.Add(missionsPanel);
            missionsPanel.BringToFront();

            AddPlaceholder();
        }

        private Label SmallLabel(string text, int x, int y)
        {
            Label label = new Label();
            label.Text = text;
            label.Location = new Point(x, y);
            label.AutoSize = true;
            label.Font = new Font("Segoe UI", 8F, FontStyle.Bold);
            label.ForeColor = Muted;
            return label;
        }

        private TextBox Input(string text, int x, int y, int width)
        {
            TextBox box = new TextBox();
            box.Text = text;
            box.Location = new Point(x, y);
            box.Size = new Size(width, 25);
            box.Font = new Font("Segoe UI", 9F, FontStyle.Regular);
            box.BackColor = Color.White;
            box.ForeColor = TextColor;
            box.BorderStyle = BorderStyle.FixedSingle;
            return box;
        }

        private Button NormalButton(string text, int x, int y, int width, Color bg, Color fg)
        {
            Button b = new Button();
            b.Text = text;
            b.Location = new Point(x, y);
            b.Size = new Size(width, 30);
            b.Font = new Font("Segoe UI", 9F, FontStyle.Bold);
            b.BackColor = bg;
            b.ForeColor = fg;
            b.FlatStyle = FlatStyle.Flat;
            b.FlatAppearance.BorderSize = 0;
            b.UseVisualStyleBackColor = false;
            b.Cursor = Cursors.Hand;
            return b;
        }

        private void AddPlaceholder()
        {
            missionsPanel.Controls.Clear();
            Panel p = CreateCard(980, 150);
            Label label = new Label();
            label.Text = "Войдите в backend DCSS, чтобы загрузить тренировочные задания.";
            label.Font = new Font("Segoe UI", 12F, FontStyle.Bold);
            label.ForeColor = Muted;
            label.AutoSize = false;
            label.TextAlign = ContentAlignment.MiddleCenter;
            label.Dock = DockStyle.Fill;
            p.Controls.Add(label);
            missionsPanel.Controls.Add(p);
        }

        private Panel CreateCard(int width, int height)
        {
            Panel p = new Panel();
            p.Width = Math.Max(900, missionsPanel.ClientSize.Width - 60);
            p.Height = height;
            p.BackColor = Card;
            p.BorderStyle = BorderStyle.FixedSingle;
            p.Margin = new Padding(0, 0, 0, 16);
            return p;
        }

        private async Task LoginAsync()
        {
            try
            {
                SetBusy(true, "Выполняется авторизация...");
                api = new DcssApiClient(txtServer.Text.Trim());
                AuthData auth = await api.LoginAsync(txtLogin.Text.Trim(), txtPassword.Text);

                if (auth.user != null)
                {
                    lblUser.Text = "Пользователь: " + auth.user.login;
                }
                else
                {
                    lblUser.Text = "Пользователь авторизован";
                }
                lblUser.ForeColor = Color.FromArgb(22, 101, 52);

                btnRefresh.Enabled = true;
                SetBusy(false, "Авторизация выполнена. Загружаю задания...");
                await LoadMissionsAsync();
            }
            catch (Exception ex)
            {
                SetBusy(false, "Ошибка авторизации.");
                MessageBox.Show(ex.Message, "Ошибка авторизации", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private async Task LoadMissionsAsync()
        {
            if (api == null || !api.IsAuthorized)
            {
                MessageBox.Show("Сначала выполните вход.", "DCSS", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            try
            {
                SetBusy(true, "Загружаю задания...");
                missionsPanel.Controls.Clear();
                runningQuestGuids.Clear();
                statusLabels.Clear();

                List<QuestTypeDto> quests = await api.GetQuestTypesAsync();

                if (quests == null || quests.Count == 0)
                {
                    Panel empty = CreateCard(980, 130);
                    Label l = new Label();
                    l.Dock = DockStyle.Fill;
                    l.Text = "Сервер не вернул задания.";
                    l.TextAlign = ContentAlignment.MiddleCenter;
                    l.Font = new Font("Segoe UI", 12F, FontStyle.Bold);
                    l.ForeColor = Muted;
                    empty.Controls.Add(l);
                    missionsPanel.Controls.Add(empty);
                }
                else
                {
                    foreach (QuestTypeDto q in quests)
                    {
                        QuestTypeDto fullQuest = q;

                        try
                        {
                            fullQuest = await api.GetQuestTypeDetailAsync(q.type_id);
                        }
                        catch
                        {
                            // Если детальный endpoint недоступен, показываем краткие данные.
                            fullQuest = q;
                        }

                        AddMissionCard(fullQuest);
                    }
                }

                SetBusy(false, "Загружено заданий: " + (quests == null ? 0 : quests.Count));
            }
            catch (Exception ex)
            {
                SetBusy(false, "Ошибка загрузки заданий.");
                MessageBox.Show(ex.Message, "Ошибка", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void AddMissionCard(QuestTypeDto quest)
        {
            Color accent = Accent(quest.type_id);
            Panel card = CreateCard(980, 175);

            Panel strip = new Panel();
            strip.BackColor = accent;
            strip.Location = new Point(16, 18);
            strip.Size = new Size(5, 136);
            card.Controls.Add(strip);

            Label title = new Label();
            title.Text = string.IsNullOrWhiteSpace(quest.name) ? "Задание " + quest.type_id : quest.name;
            title.Font = new Font("Segoe UI", 13F, FontStyle.Bold);
            title.ForeColor = TextColor;
            title.Location = new Point(36, 18);
            title.Size = new Size(620, 28);
            card.Controls.Add(title);

            Label desc = new Label();
            desc.Text = Limit(string.IsNullOrWhiteSpace(quest.desc) ? "Описание задания отсутствует." : quest.desc, 130);
            desc.Font = new Font("Segoe UI", 9F, FontStyle.Regular);
            desc.ForeColor = Muted;
            desc.Location = new Point(36, 50);
            desc.Size = new Size(650, 24);
            card.Controls.Add(desc);

            Label meta = new Label();
            meta.Text = "Тип: " + quest.type_id + "   |   Время: " + FormatTime(quest.max_time_sec);
            meta.Font = new Font("Segoe UI", 9F, FontStyle.Bold);
            meta.ForeColor = accent;
            meta.Location = new Point(36, 82);
            meta.Size = new Size(650, 22);
            card.Controls.Add(meta);

            Label criteria = new Label();
            criteria.Text = CriteriaText(quest);
            criteria.Font = new Font("Segoe UI", 8F, FontStyle.Regular);
            criteria.ForeColor = Color.FromArgb(55, 65, 81);
            criteria.Location = new Point(36, 112);
            criteria.Size = new Size(650, 44);
            card.Controls.Add(criteria);

            Label s = new Label();
            s.Text = "Не запущено";
            s.Font = new Font("Segoe UI", 8F, FontStyle.Bold);
            s.ForeColor = Muted;
            s.TextAlign = ContentAlignment.MiddleCenter;
            s.Location = new Point(card.Width - 185, 20);
            s.Size = new Size(140, 22);
            s.Anchor = AnchorStyles.Top | AnchorStyles.Right;
            card.Controls.Add(s);
            statusLabels[quest.type_id] = s;

            Button start = NormalButton("Начать", card.Width - 190, 50, 150, accent, Color.White);
            start.Anchor = AnchorStyles.Top | AnchorStyles.Right;
            start.Click += async delegate { await StartQuestAsync(quest, accent); };
            card.Controls.Add(start);

            Button stat = NormalButton("Статус", card.Width - 190, 88, 150, Color.FromArgb(235, 240, 247), TextColor);
            stat.Anchor = AnchorStyles.Top | AnchorStyles.Right;
            stat.Click += async delegate { await RefreshQuestStatusAsync(quest.type_id); };
            card.Controls.Add(stat);

            Button stop = NormalButton("Остановить", card.Width - 190, 126, 150, Red, Color.White);
            stop.Anchor = AnchorStyles.Top | AnchorStyles.Right;
            stop.Click += async delegate { await StopQuestAsync(quest.type_id); };
            card.Controls.Add(stop);

            missionsPanel.Controls.Add(card);
        }

        private async Task StartQuestAsync(QuestTypeDto quest, Color accent)
        {
            try
            {
                SetBusy(true, "Запуск задания...");
                QuestStartData started = await api.StartQuestAsync(quest.type_id);
                runningQuestGuids[quest.type_id] = started.quest_guid;

                if (statusLabels.ContainsKey(quest.type_id))
                {
                    statusLabels[quest.type_id].Text = "В процессе";
                    statusLabels[quest.type_id].ForeColor = accent;
                }

                SetBusy(false, "Задание запущено.");
                MessageBox.Show(
                    "Задание запущено.\n\nПодключение Mission Planner:\n" + started.link,
                    "DCSS",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information
                );
            }
            catch (Exception ex)
            {
                SetBusy(false, "Ошибка запуска задания.");
                MessageBox.Show(ex.Message, "Ошибка запуска", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private async Task RefreshQuestStatusAsync(int typeId)
        {
            if (!runningQuestGuids.ContainsKey(typeId))
            {
                MessageBox.Show("Для этого задания нет активного запуска.", "DCSS", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            try
            {
                SetBusy(true, "Получаю статус...");
                QuestStatusData st = await api.GetQuestStatusAsync(runningQuestGuids[typeId]);
                string text = TranslateStatus(st.status);
                if (!string.IsNullOrWhiteSpace(st.result)) text += ", " + TranslateResult(st.result);

                if (statusLabels.ContainsKey(typeId))
                {
                    statusLabels[typeId].Text = text;
                    statusLabels[typeId].ForeColor = StatusColor(st.status, st.result);
                }

                SetBusy(false, text);

                StringBuilder sb = new StringBuilder();
                if (st.checklist != null)
                {
                    foreach (ChecklistItemDto c in st.checklist)
                    {
                        sb.AppendLine(c.name + ": " + c.progress + "%");
                    }
                }

                MessageBox.Show(
                    "GUID: " + st.quest_guid + "\n" +
                    "Статус: " + TranslateStatus(st.status) + "\n" +
                    "Результат: " + TranslateResult(st.result) + "\n" +
                    "Время: " + st.elapsed_time_sec + " сек.\n\n" + sb.ToString(),
                    "Статус задания",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information
                );
            }
            catch (Exception ex)
            {
                SetBusy(false, "Ошибка получения статуса.");
                MessageBox.Show(ex.Message, "Ошибка", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private async Task StopQuestAsync(int typeId)
        {
            if (!runningQuestGuids.ContainsKey(typeId))
            {
                MessageBox.Show("Для этого задания нет активного запуска.", "DCSS", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            DialogResult dr = MessageBox.Show("Остановить задание?", "DCSS", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
            if (dr != DialogResult.Yes) return;

            try
            {
                SetBusy(true, "Остановка задания...");
                await api.StopQuestAsync(runningQuestGuids[typeId]);
                runningQuestGuids.Remove(typeId);

                if (statusLabels.ContainsKey(typeId))
                {
                    statusLabels[typeId].Text = "Остановлено";
                    statusLabels[typeId].ForeColor = Red;
                }

                SetBusy(false, "Задание остановлено.");
            }
            catch (Exception ex)
            {
                SetBusy(false, "Ошибка остановки.");
                MessageBox.Show(ex.Message, "Ошибка", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void SetBusy(bool busy, string text)
        {
            if (btnLogin != null) btnLogin.Enabled = !busy;
            if (btnRefresh != null) btnRefresh.Enabled = !busy && api != null && api.IsAuthorized;
            if (lblStatus != null)
            {
                lblStatus.Text = text;
                lblStatus.ForeColor = busy ? Blue : Muted;
            }
        }

        private Color Accent(int typeId)
        {
            if (typeId == 1) return Blue;
            if (typeId == 2) return Green;
            if (typeId == 3) return Orange;
            return Color.FromArgb(139, 92, 246);
        }

        private string CriteriaText(QuestTypeDto quest)
        {
            if (quest.checklist == null || quest.checklist.Count == 0) return "Критерии: не указаны.";
            StringBuilder sb = new StringBuilder();
            sb.Append("Критерии: ");
            int max = Math.Min(quest.checklist.Count, 3);
            for (int i = 0; i < max; i++)
            {
                if (i > 0) sb.Append(" • ");
                sb.Append(quest.checklist[i].name);
            }
            if (quest.checklist.Count > max) sb.Append(" • ...");
            return sb.ToString();
        }

        private Color StatusColor(string status, string result)
        {
            if (status == "completed" && result == "success") return Color.FromArgb(22, 163, 74);
            if (status == "completed" && result == "fail") return Red;
            if (status == "aborted") return Red;
            if (status == "running") return Orange;
            return Muted;
        }

        private string TranslateStatus(string status)
        {
            if (status == "running") return "В процессе";
            if (status == "completed") return "Завершено";
            if (status == "aborted") return "Остановлено";
            return status ?? "Неизвестно";
        }

        private string TranslateResult(string result)
        {
            if (result == "success") return "Успешно";
            if (result == "fail") return "Не выполнено";
            if (string.IsNullOrWhiteSpace(result)) return "—";
            return result;
        }

        private string FormatTime(int seconds)
        {
            if (seconds <= 0) return "не указано";
            int m = seconds / 60;
            int s = seconds % 60;
            return s == 0 ? m + " мин" : m + " мин " + s + " сек";
        }

        private string Limit(string text, int max)
        {
            if (string.IsNullOrWhiteSpace(text)) return "";
            if (text.Length <= max) return text;
            return text.Substring(0, max) + "...";
        }
    }

    public class DcssApiClient
    {
        private readonly HttpClient http;
        private string authToken;
        public bool IsAuthorized { get { return !string.IsNullOrWhiteSpace(authToken); } }

        public DcssApiClient(string baseUrl)
        {
            if (string.IsNullOrWhiteSpace(baseUrl)) throw new Exception("Backend URL не указан.");
            http = new HttpClient();
            http.BaseAddress = new Uri(baseUrl.TrimEnd('/') + "/");
            http.Timeout = TimeSpan.FromSeconds(15);
        }

        public async Task<AuthData> LoginAsync(string login, string password)
        {
            if (string.IsNullOrWhiteSpace(login)) throw new Exception("Введите логин.");
            if (string.IsNullOrWhiteSpace(password)) throw new Exception("Введите пароль.");

            try { return await LoginPostAsync(login, password); }
            catch { return await LoginGetAsync(login, password); }
        }

        private async Task<AuthData> LoginPostAsync(string login, string password)
        {
            LoginRequest body = new LoginRequest();
            body.login = login;
            body.password = password;
            string json = JsonConvert.SerializeObject(body);
            StringContent content = new StringContent(json, Encoding.UTF8, "application/json");
            HttpResponseMessage response = await http.PostAsync("auth", content);
            string text = await response.Content.ReadAsStringAsync();
            if (!response.IsSuccessStatusCode) throw new Exception(text);
            ApiResponse<AuthData> result = JsonConvert.DeserializeObject<ApiResponse<AuthData>>(text);
            if (result == null || !result.success || result.data == null) throw new Exception("Некорректный ответ авторизации POST.");
            ApplyToken(result.data.auth_token);
            return result.data;
        }

        private async Task<AuthData> LoginGetAsync(string login, string password)
        {
            string url = "auth?login=" + Uri.EscapeDataString(login) + "&password=" + Uri.EscapeDataString(password);
            HttpResponseMessage response = await http.GetAsync(url);
            string text = await response.Content.ReadAsStringAsync();
            if (!response.IsSuccessStatusCode) throw new Exception(text);
            ApiResponse<AuthData> result = JsonConvert.DeserializeObject<ApiResponse<AuthData>>(text);
            if (result == null || !result.success || result.data == null) throw new Exception("Некорректный ответ авторизации GET.");
            ApplyToken(result.data.auth_token);
            return result.data;
        }

        private void ApplyToken(string token)
        {
            if (string.IsNullOrWhiteSpace(token)) throw new Exception("Backend не вернул auth_token.");
            authToken = token;
            http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", authToken);
        }

        public async Task<List<QuestTypeDto>> GetQuestTypesAsync()
        {
            HttpResponseMessage response = await http.GetAsync("quest/type?skip=0&take=100");
            string text = await response.Content.ReadAsStringAsync();
            if (!response.IsSuccessStatusCode) throw new Exception(text);
            ApiResponse<QuestTypesData> result = JsonConvert.DeserializeObject<ApiResponse<QuestTypesData>>(text);
            if (result == null || !result.success || result.data == null) throw new Exception("Некорректный список заданий.");
            return result.data.types ?? new List<QuestTypeDto>();
        }

        public async Task<QuestTypeDto> GetQuestTypeDetailAsync(int typeId)
        {
            HttpResponseMessage response = await http.GetAsync("quest/type/" + typeId);
            string text = await response.Content.ReadAsStringAsync();
            if (!response.IsSuccessStatusCode) throw new Exception(text);

            ApiResponse<QuestTypeDto> result = JsonConvert.DeserializeObject<ApiResponse<QuestTypeDto>>(text);
            if (result == null || !result.success || result.data == null) throw new Exception("Некорректные детали задания.");

            return result.data;
        }

        public async Task<QuestStartData> StartQuestAsync(int typeId)
        {
            StartQuestRequest body = new StartQuestRequest();
            body.type_id = typeId;
            string json = JsonConvert.SerializeObject(body);
            StringContent content = new StringContent(json, Encoding.UTF8, "application/json");
            HttpResponseMessage response = await http.PostAsync("quest/start", content);
            string text = await response.Content.ReadAsStringAsync();
            if (!response.IsSuccessStatusCode) throw new Exception(text);
            ApiResponse<QuestStartData> result = JsonConvert.DeserializeObject<ApiResponse<QuestStartData>>(text);
            if (result == null || !result.success || result.data == null) throw new Exception("Некорректный ответ запуска задания.");
            return result.data;
        }

        public async Task<QuestStatusData> GetQuestStatusAsync(string questGuid)
        {
            HttpResponseMessage response = await http.GetAsync("quest/" + questGuid);
            string text = await response.Content.ReadAsStringAsync();
            if (!response.IsSuccessStatusCode) throw new Exception(text);
            ApiResponse<QuestStatusData> result = JsonConvert.DeserializeObject<ApiResponse<QuestStatusData>>(text);
            if (result == null || !result.success || result.data == null) throw new Exception("Некорректный статус задания.");
            return result.data;
        }

        public async Task StopQuestAsync(string questGuid)
        {
            HttpResponseMessage response = await http.PostAsync("quest/stop/" + questGuid, null);
            string text = await response.Content.ReadAsStringAsync();
            if (!response.IsSuccessStatusCode) throw new Exception(text);
        }
    }

    public class ApiResponse<T>
    {
        public bool success { get; set; }
        public T data { get; set; }
        public string type { get; set; }
        public string details { get; set; }
    }

    public class LoginRequest
    {
        public string login { get; set; }
        public string password { get; set; }
    }

    public class AuthData
    {
        public string auth_token { get; set; }
        public UserDto user { get; set; }
    }

    public class UserDto
    {
        public int id { get; set; }
        public string login { get; set; }
        public string email { get; set; }
        public string role { get; set; }
    }

    public class QuestTypesData
    {
        public int skip { get; set; }
        public int take { get; set; }
        public int total { get; set; }
        public List<QuestTypeDto> types { get; set; }
    }

    public class QuestTypeDto
    {
        public int type_id { get; set; }
        public string name { get; set; }
        public string desc { get; set; }
        public int max_time_sec { get; set; }
        public string markdown { get; set; }
        public List<ChecklistItemDto> checklist { get; set; }
    }

    public class ChecklistItemDto
    {
        public int check_id { get; set; }
        public string name { get; set; }
        public string desc { get; set; }
        public int progress { get; set; }
    }

    public class StartQuestRequest
    {
        public int type_id { get; set; }
    }

    public class QuestStartData
    {
        public int type_id { get; set; }
        public string name { get; set; }
        public string desc { get; set; }
        public string quest_guid { get; set; }
        public string link { get; set; }
    }

    public class QuestStatusData
    {
        public int type_id { get; set; }
        public string quest_guid { get; set; }
        public string link { get; set; }
        public string status { get; set; }
        public string result { get; set; }
        public int max_time_sec { get; set; }
        public int elapsed_time_sec { get; set; }
        public List<ChecklistItemDto> checklist { get; set; }
    }
}
