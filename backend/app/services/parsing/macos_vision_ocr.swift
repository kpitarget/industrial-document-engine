import Foundation
import PDFKit
import Vision
import AppKit

func renderPageImage(page: PDFPage, scale: CGFloat) -> CGImage? {
    let rect = page.bounds(for: .mediaBox)
    let width = max(1, Int(rect.width * scale))
    let height = max(1, Int(rect.height * scale))

    guard
        let context = CGContext(
            data: nil,
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: 0,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        )
    else {
        return nil
    }

    context.setFillColor(NSColor.white.cgColor)
    context.fill(CGRect(x: 0, y: 0, width: width, height: height))
    context.interpolationQuality = .high
    context.scaleBy(x: scale, y: scale)
    page.draw(with: .mediaBox, to: context)
    return context.makeImage()
}

func ocrText(page: PDFPage) -> String {
    guard let image = renderPageImage(page: page, scale: 3.0) else {
        return ""
    }

    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true

    do {
        try VNImageRequestHandler(cgImage: image, options: [:]).perform([request])
    } catch {
        return ""
    }

    let observations = (request.results ?? []).sorted {
        if abs($0.boundingBox.midY - $1.boundingBox.midY) > 0.01 {
            return $0.boundingBox.midY > $1.boundingBox.midY
        }
        return $0.boundingBox.minX < $1.boundingBox.minX
    }

    let lines = observations.compactMap { $0.topCandidates(1).first?.string }
    return lines.joined(separator: "\n")
}

if CommandLine.arguments.count < 2 {
    fputs("Usage: swift macos_vision_ocr.swift <pdf_path>\n", stderr)
    exit(1)
}

let pdfPath = CommandLine.arguments[1]
let pdfURL = URL(fileURLWithPath: pdfPath)

guard let document = PDFDocument(url: pdfURL) else {
    fputs("Unable to open PDF: \(pdfPath)\n", stderr)
    exit(2)
}

var pages: [String] = []
for pageIndex in 0..<document.pageCount {
    guard let page = document.page(at: pageIndex) else {
        continue
    }

    if let nativeText = page.string, !nativeText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
        pages.append(nativeText)
    } else {
        pages.append(ocrText(page: page))
    }
}

print(pages.joined(separator: "\n\n"))
