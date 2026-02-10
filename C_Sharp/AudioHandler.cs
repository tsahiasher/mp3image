using System;
using System.IO;
using TagLib;

namespace ID3Editor
{
    public static class AudioHandler
    {
        public record Mp3Tags(string? Title, string? Artist, byte[]? CoverArt);

        public static Mp3Tags ReadTags(string mp3Path)
        {
            if (!System.IO.File.Exists(mp3Path))
                throw new FileNotFoundException($"MP3 file not found: {mp3Path}");

            try
            {
                using var file = TagLib.File.Create(mp3Path);
                var title = file.Tag.Title;
                var artist = file.Tag.FirstPerformer; // TagLib uses FirstPerformer for Artist in many cases, or Performers array
                
                byte[]? coverArt = null;
                if (file.Tag.Pictures.Length > 0)
                {
                    coverArt = file.Tag.Pictures[0].Data.Data;
                }

                return new Mp3Tags(title, artist, coverArt);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error reading tags from {mp3Path}: {ex.Message}");
                // Return empty/null values on error, or rethrow? 
                // Creating a new file object might fail if it's locked.
                // For safety, let's rethrow so the UI knows something went wrong.
                throw;
            }
        }

        public static byte[]? ExtractCoverArt(string mp3Path)
        {
             // maintain backward compatibility or just use ReadTags
             return ReadTags(mp3Path).CoverArt;
        }

        public static void SaveTags(string mp3Path, string? imagePath, string title, string artist)
        {
            if (!System.IO.File.Exists(mp3Path))
                throw new FileNotFoundException($"MP3 file not found: {mp3Path}");

            try
            {
                // Force ID3v2.3 default before writing
                TagLib.Id3v2.Tag.DefaultVersion = 3;
                TagLib.Id3v2.Tag.ForceDefaultVersion = true;

                using var file = TagLib.File.Create(mp3Path);
                
                // Update Text Tags
                file.Tag.Title = title;
                file.Tag.Performers = new[] { artist };

                // Update Image if provided
                if (!string.IsNullOrEmpty(imagePath) && System.IO.File.Exists(imagePath))
                {
                     var picture = new Picture(imagePath)
                    {
                         Type = PictureType.FrontCover,
                         Description = "Cover"
                    };
                    file.Tag.Pictures = new IPicture[] { picture };
                }
                // If imagePath is null/empty, we DO NOT remove existing pictures, 
                // unless the user explicitly wants to remove them (not in reqs).
                // The requirements say "Allow to edit it and save it".
                // If the user drops an image, we replace it. If they don't, should we keep the old one?
                // The previous code `EmbedCoverArt` REPLACED existing pictures.
                // The new requirement is "Show current tag content... allow to edit... save".
                // If I just edit text, I should probably preserve the image unless a new one is dropped.
                // But the `MainForm` has `currentImagePath` which is set when a new image is dropped.
                // So if `currentImagePath` is set, we update the image. If not, we leave it alone?
                // Wait, the previous logic was ONLY about embedding cover art.
                // Effectively, if we pass `currentImagePath`, we update it.
                
                file.Save();
                Console.WriteLine($"Successfully saved tags to {mp3Path}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error writing tags to {mp3Path}: {ex.Message}");
                throw;
            }
        }

        public static void EmbedCoverArt(string mp3Path, string imagePath)
        {
            // Forward to SaveTags with current tags to avoid clearing them?
            // Or just use the old logic? 
            // Better to keep this for backward compat if needed, but we will likely replace usage in MainForm.
            // Actually, we can just implement it using the new logic if we want, or leave it.
            // But verify: The user wanted "Add id3 tag editor... Show current... edit... save".
            // So we will use SaveTags in MainForm. 
            // I will keep EmbedCoverArt implementation as is or redirect it, but I'll replace the class content completely to keep it clean.
            
            // Re-implementing EmbedCoverArt to just call SaveTags logic would be cleaner but 
            // SaveTags needs title/artist.
            
            // For now, I'll just leave `EmbedCoverArt` as deprecated or remove it if I replace the whole file content.
            // I will Replace the whole file content with the new structure.
             if(!System.IO.File.Exists(mp3Path)) throw new FileNotFoundException(mp3Path);
             if(!System.IO.File.Exists(imagePath)) throw new FileNotFoundException(imagePath);
             
             // We can read, then update image, then save.
             var tags = ReadTags(mp3Path);
             SaveTags(mp3Path, imagePath, tags.Title ?? "", tags.Artist ?? "");
        }
    }
}
