using System;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Windows.Forms;

namespace ID3Editor
{
    public class MainForm : Form
    {
        private Label mp3Label;
        private Label imageLabel;
        private TextBox titleBox;
        private TextBox artistBox;
        private Button saveButton;

        private string? currentMp3Path;
        private string? currentImagePath;

        public MainForm()
        {
            InitializeComponent();
            LoadAppIcon();
        }

        private void LoadAppIcon()
        {
            try 
            {
                var assembly = System.Reflection.Assembly.GetExecutingAssembly();
                // Resource name is usually Namespace.Filename
                using var stream = assembly.GetManifestResourceStream("ID3Editor.icon.ico");
                if (stream != null)
                {
                    this.Icon = new Icon(stream);
                }
            }
            catch { /* Ignore if icon fails, fallback to default */ }
        }

        private void InitializeComponent()
        {
            this.Text = "ID3 Cover Art Editor";
            this.Size = new Size(800, 600); // Increased height for new fields
            this.StartPosition = FormStartPosition.CenterScreen;

            // Container for layout
            var layoutPanel = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 2,
                RowCount = 5, // Drops, Title, Artist, Save
                Padding = new Padding(20),
            };
            layoutPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
            layoutPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
            
            // Row definitions
            layoutPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 60)); // Drops area
            layoutPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 30)); // Title Label
            layoutPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 40)); // Title Box
            layoutPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 30)); // Artist Label
            layoutPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 40)); // Artist Box
            layoutPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 60)); // Save Button

            // MP3 Drop Label
            mp3Label = CreateDropLabel("Drop MP3 File Here\n(or click to open)");
            mp3Label.Click += (s, e) => OpenMp3Dialog();
            
            // Image Drop Label
            imageLabel = CreateDropLabel("Drop New Image Here\n(or click to open)");
            imageLabel.Click += (s, e) => OpenImageDialog();

            // Title Controls
            var titleLabel = new Label { Text = "Title:", Dock = DockStyle.Bottom, Font = new Font("Segoe UI", 9, FontStyle.Bold) };
            titleBox = new TextBox { Dock = DockStyle.Fill, Font = new Font("Segoe UI", 10) };
            titleBox.RightToLeft = RightToLeft.No; // Allow Hebrew but keeps standard LTR alignment usually preferred for tech/mixed, or maybe Yes for Hebrew?
            // User asked for Hebrew text support. usually standard TextBox supports it. 

            // Artist Controls
            var artistLabel = new Label { Text = "Artist:", Dock = DockStyle.Bottom, Font = new Font("Segoe UI", 9, FontStyle.Bold) };
            artistBox = new TextBox { Dock = DockStyle.Fill, Font = new Font("Segoe UI", 10) };

            // Save Button
            saveButton = new Button
            {
                Text = "Save Changes",
                Dock = DockStyle.Fill,
                Enabled = false,
                Font = new Font("Segoe UI", 12, FontStyle.Bold),
                Height = 50,
                BackColor = Color.LightGray
            };
            saveButton.Click += SaveButton_Click;

            // Add controls to layout
            // Row 0: Drops
            layoutPanel.Controls.Add(mp3Label, 0, 0);
            layoutPanel.Controls.Add(imageLabel, 1, 0);
            
            // Row 1: Title Label (span 2)
            layoutPanel.Controls.Add(titleLabel, 0, 1);
            layoutPanel.SetColumnSpan(titleLabel, 2);

            // Row 2: Title Box (span 2)
            layoutPanel.Controls.Add(titleBox, 0, 2);
            layoutPanel.SetColumnSpan(titleBox, 2);

            // Row 3: Artist Label (span 2)
            layoutPanel.Controls.Add(artistLabel, 0, 3);
            layoutPanel.SetColumnSpan(artistLabel, 2);

            // Row 4: Artist Box (span 2)
            layoutPanel.Controls.Add(artistBox, 0, 4);
            layoutPanel.SetColumnSpan(artistBox, 2);

            // Row 5: Save Button (span 2)
            layoutPanel.Controls.Add(saveButton, 0, 5);
            layoutPanel.SetColumnSpan(saveButton, 2);

            this.Controls.Add(layoutPanel);
        }

        private Label CreateDropLabel(string text)
        {
            var label = new Label
            {
                Text = text,
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleCenter,
                AllowDrop = true,
                BackColor = Color.WhiteSmoke,
                BorderStyle = BorderStyle.FixedSingle,
                Font = new Font("Segoe UI", 10),
                Cursor = Cursors.Hand,
                Margin = new Padding(10)
            };
            
            label.DragEnter += Label_DragEnter;
            label.DragDrop += Label_DragDrop;
            
            return label;
        }

        private void Label_DragEnter(object? sender, DragEventArgs e)
        {
            if (e.Data != null && e.Data.GetDataPresent(DataFormats.FileDrop))
                e.Effect = DragDropEffects.Copy;
            else
                e.Effect = DragDropEffects.None;
        }

        private void Label_DragDrop(object? sender, DragEventArgs e)
        {
            if (e.Data == null || !e.Data.GetDataPresent(DataFormats.FileDrop)) return;
            
            var files = (string[]?)e.Data.GetData(DataFormats.FileDrop);
            if (files == null || files.Length == 0) return;
            
            var file = files[0];
            HandleFileDrop((Label)sender!, file);
        }

        private void OpenMp3Dialog()
        {
            using var ofd = new OpenFileDialog { Filter = "MP3 Files|*.mp3|All Files|*.*" };
            if (ofd.ShowDialog() == DialogResult.OK)
            {
                HandleFileDrop(mp3Label, ofd.FileName);
            }
        }

        private void OpenImageDialog()
        {
             using var ofd = new OpenFileDialog { Filter = "Image Files|*.jpg;*.jpeg;*.png|All Files|*.*" };
            if (ofd.ShowDialog() == DialogResult.OK)
            {
                HandleFileDrop(imageLabel, ofd.FileName);
            }
        }

        private void HandleFileDrop(Label sender, string filePath)
        {
            string ext = Path.GetExtension(filePath).ToLower();

            if (sender == mp3Label)
            {
                if (ext == ".mp3")
                {
                    currentMp3Path = filePath;
                    mp3Label.Text = $"MP3 Loaded:\n{Path.GetFileName(filePath)}";
                    LoadMp3Data();
                    UpdateSaveState();
                }
            }
            else if (sender == imageLabel)
            {
                if (new[] { ".jpg", ".jpeg", ".png" }.Contains(ext))
                {
                    currentImagePath = filePath;
                    ShowImage(filePath);
                    UpdateSaveState();
                }
            }
        }

        private void LoadMp3Data()
        {
            if (string.IsNullOrEmpty(currentMp3Path)) return;

            try
            {
                var tags = AudioHandler.ReadTags(currentMp3Path);
                
                // Handle Cover Art
                if (tags.CoverArt != null)
                {
                    ShowImageFromData(tags.CoverArt);
                    currentImagePath = null; // Reset pending image
                }
                else if (imageLabel.BackgroundImage == null)
                {
                    ClearLabelImage();
                    imageLabel.Text = "No existing cover art found.\nDrop a new image here.";
                }

                // Handle Title Default
                if (string.IsNullOrWhiteSpace(tags.Title))
                {
                    titleBox.Text = Path.GetFileNameWithoutExtension(currentMp3Path);
                }
                else
                {
                    titleBox.Text = tags.Title;
                }

                // Handle Artist Default
                if (string.IsNullOrWhiteSpace(tags.Artist))
                {
                    artistBox.Text = "סרקאסטים: אורן וצחי";
                }
                else
                {
                    artistBox.Text = tags.Artist;
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error reading MP3: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void ClearLabelImage()
        {
            if (imageLabel.BackgroundImage != null)
            {
                imageLabel.BackgroundImage.Dispose();
                imageLabel.BackgroundImage = null;
            }
            imageLabel.Image = null; // Also clear foreground image just in case
        }

        private void ShowImage(string path)
        {
            try
            {
                using var stream = new FileStream(path, FileMode.Open, FileAccess.Read);
                var img = Image.FromStream(stream);
                SetLabelImage(img);
            }
            catch {
                ClearLabelImage();
                imageLabel.Text = "Failed to load image.";
            }
        }

        private void ShowImageFromData(byte[] data)
        {
             try
            {
                using var ms = new MemoryStream(data);
                var img = Image.FromStream(ms);
                SetLabelImage(img);
            }
            catch {
                ClearLabelImage();
                 imageLabel.Text = "Failed to load existing cover art.";
            }

        }

        private void SetLabelImage(Image img)
        {
             ClearLabelImage();
             
             // Create a copy to avoid stream issues if original stream is closed
             // and set as background image to support zooming
             imageLabel.BackgroundImage = new Bitmap(img);
             imageLabel.BackgroundImageLayout = ImageLayout.Zoom;
             
             imageLabel.Text = ""; // Clear text
        }

        private void UpdateSaveState()
        {
            // Now we allow save if MP3 is loaded, even if no new image (we might allow editing text)
            saveButton.Enabled = !string.IsNullOrEmpty(currentMp3Path);
            saveButton.BackColor = saveButton.Enabled ? Color.LightGreen : Color.LightGray;
        }

        private void SaveButton_Click(object? sender, EventArgs e)
        {
            if (string.IsNullOrEmpty(currentMp3Path)) return;

            try
            {
                AudioHandler.SaveTags(currentMp3Path, currentImagePath, titleBox.Text, artistBox.Text);
                MessageBox.Show("Tags and Cover art updated successfully!", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
                
                // Refresh
                LoadMp3Data();
                currentImagePath = null;
                UpdateSaveState();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to save: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }
}
