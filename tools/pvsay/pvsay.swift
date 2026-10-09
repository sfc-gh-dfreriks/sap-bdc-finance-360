// pvsay — speak text with a macOS Personal Voice (or any system voice) and write it to an audio file.
//
//   pvsay --status                      request Personal Voice access; print status and personal voices
//   pvsay --list                        list all English voices (personal voices marked *)
//   pvsay [-v NAME] [-r WPM] -o OUT TEXT
//         -v  voice name; default = first Personal Voice
//         -r  words per minute, as in `say` (default 175 ≈ the system default speaking rate)
//         -o  output file (.caf/.wav/.aiff); written at the synthesizer's native format
//
// Exit codes: 0 ok, 2 bad usage, 3 not authorized, 4 no matching voice, 5 synthesis failed.
import AVFoundation
import Foundation

func fail(_ msg: String, _ code: Int32) -> Never {
    FileHandle.standardError.write((msg + "\n").data(using: .utf8)!)
    exit(code)
}

func authorize() -> AVSpeechSynthesizer.PersonalVoiceAuthorizationStatus {
    let sem = DispatchSemaphore(value: 0)
    var result = AVSpeechSynthesizer.personalVoiceAuthorizationStatus
    if result == .notDetermined {
        AVSpeechSynthesizer.requestPersonalVoiceAuthorization { s in result = s; sem.signal() }
        // the system shows a permission dialog; wait for the user's answer
        while sem.wait(timeout: .now() + 0.1) == .timedOut {
            RunLoop.current.run(until: Date().addingTimeInterval(0.1))
        }
    }
    return result
}

func statusName(_ s: AVSpeechSynthesizer.PersonalVoiceAuthorizationStatus) -> String {
    switch s {
    case .authorized: return "authorized"
    case .denied: return "denied"
    case .notDetermined: return "notDetermined"
    case .unsupported: return "unsupported"
    @unknown default: return "unknown"
    }
}

func personalVoices() -> [AVSpeechSynthesisVoice] {
    AVSpeechSynthesisVoice.speechVoices().filter { $0.voiceTraits.contains(.isPersonalVoice) }
}

var args = Array(CommandLine.arguments.dropFirst())
if args.isEmpty { fail("usage: pvsay --status | --list | [-v NAME] [-r WPM] -o OUT TEXT", 2) }

if args == ["--status"] {
    let s = authorize()
    print("authorization: \(statusName(s))")
    for v in personalVoices() { print("personal voice: \(v.name)\t\(v.identifier)") }
    if s == .authorized && personalVoices().isEmpty { print("no Personal Voice found — create one in System Settings ▸ Accessibility ▸ Personal Voice") }
    exit(s == .authorized ? 0 : 3)
}

if args == ["--list"] {
    _ = authorize()
    for v in AVSpeechSynthesisVoice.speechVoices() where v.language.hasPrefix("en") {
        let mark = v.voiceTraits.contains(.isPersonalVoice) ? "*" : " "
        print("\(mark) \(v.name)\t\(v.language)\t\(v.identifier)")
    }
    exit(0)
}

var voiceName: String? = nil, wpm = 175.0, out: String? = nil, words: [String] = []
while !args.isEmpty {
    let a = args.removeFirst()
    switch a {
    case "-v": voiceName = args.isEmpty ? nil : args.removeFirst()
    case "-r": wpm = Double(args.isEmpty ? "" : args.removeFirst()) ?? 175
    case "-o": out = args.isEmpty ? nil : args.removeFirst()
    default: words.append(a)
    }
}
guard let outPath = out, !words.isEmpty else { fail("need -o OUT and TEXT", 2) }

let auth = authorize()
let all = AVSpeechSynthesisVoice.speechVoices()
let voice: AVSpeechSynthesisVoice
if let n = voiceName {
    guard let v = all.first(where: { $0.name == n || $0.identifier == n }) else { fail("voice not found: \(n)", 4) }
    voice = v
} else {
    guard auth == .authorized else { fail("Personal Voice not authorized (\(statusName(auth))). Run: pvsay --status", 3) }
    guard let v = personalVoices().first else { fail("no Personal Voice found — create one in System Settings ▸ Accessibility ▸ Personal Voice", 4) }
    voice = v
}
if voice.voiceTraits.contains(.isPersonalVoice) && auth != .authorized {
    fail("Personal Voice not authorized (\(statusName(auth))). Run: pvsay --status", 3)
}

let utt = AVSpeechUtterance(string: words.joined(separator: " "))
utt.voice = voice
// AVSpeechUtteranceDefaultSpeechRate corresponds to roughly 175 wpm; scale linearly and clamp.
utt.rate = min(AVSpeechUtteranceMaximumSpeechRate,
               max(AVSpeechUtteranceMinimumSpeechRate, Float(Double(AVSpeechUtteranceDefaultSpeechRate) * wpm / 175.0)))

let synth = AVSpeechSynthesizer()
var file: AVAudioFile? = nil
var done = false, frames: AVAudioFrameCount = 0, err: String? = nil
synth.write(utt) { buffer in
    guard let pcm = buffer as? AVAudioPCMBuffer else { return }
    if pcm.frameLength == 0 { done = true; return }   // end of stream
    do {
        if file == nil {
            file = try AVAudioFile(forWriting: URL(fileURLWithPath: outPath), settings: pcm.format.settings,
                                   commonFormat: pcm.format.commonFormat, interleaved: pcm.format.isInterleaved)
        }
        try file!.write(from: pcm)
        frames += pcm.frameLength
    } catch { err = "\(error)"; done = true }
}
let deadline = Date().addingTimeInterval(600)
while !done && Date() < deadline { RunLoop.current.run(until: Date().addingTimeInterval(0.05)) }
if let e = err { fail("write failed: \(e)", 5) }
if frames == 0 { fail("synthesis produced no audio (voice: \(voice.name))", 5) }
print("wrote \(outPath) voice=\(voice.name) frames=\(frames)")
