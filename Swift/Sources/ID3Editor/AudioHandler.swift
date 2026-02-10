import Foundation
import ID3TagEditor

struct Mp3Tags {
    var title: String?
    var artist: String?
    var coverArt: Data?
}

class AudioHandler {
    private let id3TagEditor = ID3TagEditor()

    func readTags(from path: String) throws -> Mp3Tags {
        // ID3TagEditor loads the tag
        // If file doesn't exist, throw
        guard FileManager.default.fileExists(atPath: path) else {
            throw NSError(domain: "FileNotFound", code: 404, userInfo: [NSLocalizedDescriptionKey: "File not found: \(path)"])
        }

        let id3Tag = try id3TagEditor.read(from: path)
        
        var title: String? = nil
        if let titleFrame = id3Tag?.frames[.title] as? ID3FrameWithStringContent {
            title = titleFrame.content
        }
        
        var artist: String? = nil
        if let artistFrame = id3Tag?.frames[.artist] as? ID3FrameWithStringContent {
            artist = artistFrame.content
        }
        // Fallback checks for other frames like 'performer' if 'artist' is missing?
        // C# TagLib uses 'FirstPerformer'. ID3TagEditor has .artist
        
        var coverArt: Data? = nil
        if let pictureFrame = id3Tag?.frames[.attachedPicture(.frontCover)] as? ID3FrameAttachedPicture {
            coverArt = pictureFrame.picture
        }
        
        return Mp3Tags(title: title, artist: artist, coverArt: coverArt)
    }

    func saveTags(to path: String, imagePath: String?, title: String, artist: String) throws {
        guard FileManager.default.fileExists(atPath: path) else {
            throw NSError(domain: "FileNotFound", code: 404, userInfo: [NSLocalizedDescriptionKey: "File not found: \(path)"])
        }
        
        // Read existing tag to preserve other fields, or create new if valid
        var id3Tag = (try? id3TagEditor.read(from: path)) ?? ID32v3TagBuilder().build()
        
        // Update Title
        id3Tag.frames[.title] = ID3FrameWithStringContent(content: title)
        
        // Update Artist
        id3Tag.frames[.artist] = ID3FrameWithStringContent(content: artist)
        
        // Update Cover Art if provided
        if let imagePath = imagePath, FileManager.default.fileExists(atPath: imagePath) {
            let imageUrl = URL(fileURLWithPath: imagePath)
            if let imageData = try? Data(contentsOf: imageUrl) {
                // Determine format based on extension or mime type?
                // ID3FrameAttachedPicture requires format. .jpeg or .png
                let ext = imageUrl.pathExtension.lowercased()
                let format: ID3PictureFormat = (ext == "png") ? .png : .jpeg
                
                id3Tag.frames[.attachedPicture(.frontCover)] = ID3FrameAttachedPicture(picture: imageData, type: .frontCover, format: format)
            }
        }
        
        try id3TagEditor.write(tag: id3Tag, to: path)
    }
}
