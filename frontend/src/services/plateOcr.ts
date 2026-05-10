import Tesseract from "tesseract.js";

export async function ocrPlate(blob: Blob): Promise<string> {
  const { data: { text } } = await Tesseract.recognize(blob, "eng");
  return text.trim();
}
