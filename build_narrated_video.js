const gTTS = require('gtts');
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const ffmpegPath = require('ffmpeg-static');

const artifactDir = "/config/.gemini/antigravity/brain/2f4261a8-5685-4bfd-afce-b34b9f4e2bbd";
const inputWebm = path.join(artifactDir, "proposalcraft_demo.webm");
const outputNarratedMp4 = path.join(artifactDir, "proposalcraft_demo_narrated.mp4");
const outputNarratedWebm = path.join(artifactDir, "proposalcraft_demo_narrated.webm");

const narrations = [
  {
    time: 1, // Start at 1s
    text: "Welcome to ProposalCraft AI, an intelligent co-pilot built with Google's Agent Development Kit for solution architects and project managers.",
    file: "part1.mp3"
  },
  {
    time: 10, // Start at 10s
    text: "First, we request a project effort estimation. ProposalCraft AI calculates 18 person-months, an 18-week timeline, phase breakdowns, and budget in USD, rendering the output using responsive A2UI card components.",
    file: "part2.mp3"
  },
  {
    time: 25, // Start at 25s
    text: "Next, we perform a multi-tool query: fetching proposal record PROP-101 from Google Cloud Firestore, then requesting a visual architecture blueprint generated with Gemini Image Generation.",
    file: "part3.mp3"
  },
  {
    time: 44, // Start at 44s
    text: "The architecture diagram is uploaded directly to Google Cloud Storage. Users can click to zoom in with the Lightbox modal, and copy or export proposal scopes directly.",
    file: "part4.mp3"
  }
];

function generateAudioFiles() {
  return Promise.all(narrations.map(n => {
    return new Promise((resolve, reject) => {
      const gtts = new gTTS(n.text, 'en');
      gtts.save(n.file, (err) => {
        if (err) return reject(err);
        console.log(`Generated ${n.file}`);
        resolve();
      });
    });
  }));
}

(async () => {
  try {
    console.log("Generating voice narration clips with gTTS...");
    await generateAudioFiles();

    console.log("Combining narration audio with ffmpeg...");
    const inputs = narrations.map(n => `-i "${n.file}"`).join(" ");
    const filterDelays = narrations.map((n, idx) => `[${idx}:a]adelay=${n.time * 1000}|${n.time * 1000}[a${idx}]`).join("; ");
    const filterMix = narrations.map((_, idx) => `[a${idx}]`).join("") + `amix=inputs=${narrations.length}:duration=longest[aout]`;
    
    const filterComplex = `"${filterDelays}; ${filterMix}"`;
    const mixCmd = `"${ffmpegPath}" -y ${inputs} -filter_complex ${filterComplex} -map "[aout]" combined_narration.mp3`;
    
    console.log("Executing ffmpeg audio mix...");
    execSync(mixCmd, { stdio: 'inherit' });

    console.log("Merging narration audio track into WebM video...");
    const mergeCmdWebm = `"${ffmpegPath}" -y -i "${inputWebm}" -i combined_narration.mp3 -c:v copy -c:a libopus -b:a 128k -shortest "${outputNarratedWebm}"`;
    execSync(mergeCmdWebm, { stdio: 'inherit' });

    console.log("Transcoding narrated video to MP4 format...");
    const mergeCmdMp4 = `"${ffmpegPath}" -y -i "${inputWebm}" -i combined_narration.mp3 -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest "${outputNarratedMp4}"`;
    execSync(mergeCmdMp4, { stdio: 'inherit' });

    // Copy narrated webm over the primary demo webm file
    fs.copyFileSync(outputNarratedWebm, inputWebm);

    console.log("Narrated video successfully created!");
    console.log(`Narrated WebM: ${outputNarratedWebm}`);
    console.log(`Narrated MP4: ${outputNarratedMp4}`);
  } catch (err) {
    console.error("Error creating narrated video:", err);
    process.exit(1);
  }
})();
