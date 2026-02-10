import SwiftUI
import UniformTypeIdentifiers

struct ContentView: View {
    @State private var currentMp3Path: String?
    @State private var currentImagePath: String?
    
    @State private var title: String = ""
    @State private var artist: String = ""
    @State private var coverArtImage: NSImage?
    
    @State private var message: String = "Drop MP3 File Here"
    @State private var errorMessage: String?
    
    let audioHandler = AudioHandler()
    
    var body: some View {
        VStack(spacing: 20) {
            // Drop Areas
            HStack(spacing: 20) {
                // MP3 Drop Zone
                DropZone(text: currentMp3Path == nil ? "Drop MP3 Here" : "MP3 Loaded: \(URL(fileURLWithPath: currentMp3Path!).lastPathComponent)",
                         allowedTypes: [.audio],
                         onDrop: handleMp3Drop)
                
                // Image Drop Zone
                DropZone(text: "Drop New Image Here",
                         allowedTypes: [.image],
                         onDrop: handleImageDrop)
            }
            .frame(height: 150)
            
            // Cover Art Display
            if let coverArtImage = coverArtImage {
                Image(nsImage: coverArtImage)
                    .resizable()
                    .scaledToFit()
                    .frame(height: 200)
            } else {
                Rectangle()
                    .fill(Color.gray.opacity(0.2))
                    .frame(height: 200)
                    .overlay(Text("No Cover Art"))
            }
            
            // Text Fields
            Form {
                TextField("Title", text: $title)
                TextField("Artist", text: $artist)
            }
            .padding()
            
            // Save Button
            Button(action: saveTags) {
                Text("Save Changes")
                    .font(.headline)
                    .frame(maxWidth: .infinity)
                    .padding()
            }
            .disabled(currentMp3Path == nil)
            
            if let errorMessage = errorMessage {
                Text(errorMessage)
                    .foregroundColor(.red)
            }
        }
        .padding()
        .frame(minWidth: 600, minHeight: 600)
    }
    
    // Logic
    private func handleMp3Drop(_ url: URL) {
        currentMp3Path = url.path
        loadMp3Data()
    }
    
    private func handleImageDrop(_ url: URL) {
        currentImagePath = url.path
        if let image = NSImage(contentsOf: url) {
            coverArtImage = image
        }
        // If they drop an image, we assume they want to use it, replacing whatever was there.
    }
    
    private func loadMp3Data() {
        guard let path = currentMp3Path else { return }
        
        do {
            let tags = try audioHandler.readTags(from: path)
            
            // Title
            if let existingTitle = tags.title, !existingTitle.isEmpty {
                title = existingTitle
            } else {
                title = URL(fileURLWithPath: path).deletingPathExtension().lastPathComponent
            }
            
            // Artist
            if let existingArtist = tags.artist, !existingArtist.isEmpty {
                artist = existingArtist
            } else {
                artist = "סרקאסטים: אורן וצחי"
            }
            
            // Cover Art
            if let data = tags.coverArt, let image = NSImage(data: data) {
                coverArtImage = image
            } else {
                coverArtImage = nil
            }
            
            errorMessage = nil
        } catch {
            errorMessage = "Error reading MP3: \(error.localizedDescription)"
        }
    }
    
    private func saveTags() {
        guard let path = currentMp3Path else { return }
        
        do {
            try audioHandler.saveTags(to: path,
                                    imagePath: currentImagePath,
                                    title: title,
                                    artist: artist)
            
            // Reload to verify and update UI state
            loadMp3Data()
            currentImagePath = nil // Clear pending image path
            
            // Show success (handled by reload usually, but we could show a toast)
        } catch {
            errorMessage = "Failed to save: \(error.localizedDescription)"
        }
    }
}

// Helper DropZone
struct DropZone: View {
    let text: String
    let allowedTypes: [UTType]
    let onDrop: (URL) -> Void
    
    @State private var isTargeted = false
    
    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 10)
                .stroke(isTargeted ? Color.accentColor : Color.gray, lineWidth: 2)
                .background(Color.gray.opacity(0.1))
            
            Text(text)
                .multilineTextAlignment(.center)
        }
        .onDrop(of: allowedTypes, isTargeted: $isTargeted) { providers in
            guard let provider = providers.first else { return false }
            
            _ = provider.loadDataRepresentation(forTypeIdentifier: allowedTypes.first?.identifier ?? "") { data, error in
                // Standard URL loading for file drops often simpler via loadObject if FileRepresentation
                // But for Drop in SwiftUI with file URLs:
            }
            
            // Simpler handling for file URLs
            if provider.hasItemConformingToTypeIdentifier(UTType.fileURL.identifier) {
                provider.loadItem(forTypeIdentifier: UTType.fileURL.identifier, options: nil) { (item, error) in
                    if let data = item as? Data, let url = URL(dataRepresentation: data, relativeTo: nil) {
                        DispatchQueue.main.async {
                            onDrop(url)
                        }
                    } else if let url = item as? URL {
                         DispatchQueue.main.async {
                            onDrop(url)
                        }
                    }
                }
                return true
            }
            return false
        }
    }
}
