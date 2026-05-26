import argparse
import distutils.util
import re 
import pickle
import textwrap
from pathlib import Path
from philter import Philter
import gzip
import json


def main():
    def _write_text_to_pdf(text: str, output_pdf: Path) -> None:
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            from reportlab.pdfgen import canvas
        except ImportError as exc:
            raise ImportError(
                "PDF export requires reportlab. Install with: pip install reportlab"
            ) from exc

        page_width, page_height = letter
        margin_left = 0.75 * inch
        margin_top = 0.75 * inch
        margin_bottom = 0.75 * inch
        line_height = 12
        wrap_width = 105

        pdf = canvas.Canvas(str(output_pdf), pagesize=letter)
        pdf.setFont("Courier", 10)

        y = page_height - margin_top
        for raw_line in text.splitlines():
            wrapped_lines = textwrap.wrap(raw_line, width=wrap_width) or [""]
            for line in wrapped_lines:
                if y <= margin_bottom:
                    pdf.showPage()
                    pdf.setFont("Courier", 10)
                    y = page_height - margin_top
                pdf.drawString(margin_left, y, line)
                y -= line_height

        pdf.save()

    def _export_output_txts_to_pdf(output_dir: str) -> int:
        out_path = Path(output_dir)
        if not out_path.exists() or not out_path.is_dir():
            return 0

        converted = 0
        for txt_file in sorted(out_path.glob("*.txt")):
            text = txt_file.read_text(encoding="utf-8", errors="replace")
            pdf_file = txt_file.with_suffix(".pdf")
            _write_text_to_pdf(text, pdf_file)
            converted += 1

        return converted

    # get input/output/filename
    help_str = """ Philter -- PHI filter for clinical notes """
    ap = argparse.ArgumentParser(description=help_str)
    ap.add_argument("-i", "--input", default="./data/i2b2_notes/",
                    help="Path to the directory or the file that contains the PHI note, the default is ./data/i2b2_notes/",
                    type=str)
    ap.add_argument("-a", "--anno", default="./data/i2b2_anno/",
                    help="Path to the directory or the file that contains the PHI annotation, the default is ./data/i2b2_anno/",
                    type=str)
    ap.add_argument("-o", "--output", default="./data/i2b2_results/",
                    help="Path to the directory to save the PHI-reduced notes in, the default is ./data/i2b2_results/",
                    type=str)
    ap.add_argument("-f", "--filters", default="./configs/integration_1.json",
                    help="Path to our config file, the default is ./configs/integration_1.json",
                    type=str)
    ap.add_argument("-x", "--xml", default="./data/phi_notes.json",
                    help="Path to the json file that contains all xml data",
                    type=str)
    ap.add_argument("-c", "--coords", default="./data/coordinates.json",
                    help="Path to the json file that contains the coordinate map data",
                    type=str)
    ap.add_argument("--eval_output", default="./data/phi/",
                    help="Path to the directory that the detailed eval files will be outputted to",
                    type=str)
    ap.add_argument("-v", "--verbose", default=True,
                    help="When verbose is true, will emit messages about script progress",
                    type=lambda x:bool(distutils.util.strtobool(x)))
    ap.add_argument("-e", "--run_eval", default=True,
                    help="When run_eval is true, will run our eval script and emit summarized results to terminal",
                    type=lambda x:bool(distutils.util.strtobool(x)))
    ap.add_argument("-t", "--freq_table", default=False,
                    help="When freqtable is true, will output a unigram/bigram frequency table of all note words and their PHI/non-PHI counts",
                    type=lambda x:bool(distutils.util.strtobool(x))) 
    ap.add_argument("-n", "--initials", default=True,
                    help="When initials is true, will include initials PHI in recall/precision calculations",
                    type=lambda x:bool(distutils.util.strtobool(x))) 
    ap.add_argument("--outputformat", default="i2b2",
                    help="Define format of annotation, allowed values are \"asterisk\", \"i2b2\". Default is \"asterisk\"",
                    type=str)
    ap.add_argument("--ucsfformat", default=False,
                    help="When ucsfformat is true, will adjust eval script for slightly different xml format",
                    type=lambda x:bool(distutils.util.strtobool(x)))
    ap.add_argument("--prod", default=False,
                    help="When prod is true, this will run the script with output in i2b2 xml format without running the eval script",
                    type=lambda x:bool(distutils.util.strtobool(x)))
    ap.add_argument("--cachepos", default=None,
                    help="Path to a directoy to store/load the pos data for all notes. If no path is specified then memory caching will be used.",
                    type=str)
    ap.add_argument("--pdf_output", default=False,
                    help="When true, creates PDF copies for redacted .txt outputs in the output directory.",
                    type=lambda x:bool(distutils.util.strtobool(x)))

    args = ap.parse_args()
    run_eval = args.run_eval
    verbose = args.verbose

    if args.prod:
        run_eval = False
        verbose = False

        philter_config = {
            "verbose":verbose,
            "run_eval":run_eval,
            "finpath":args.input,
            "foutpath":args.output,
            "outformat":args.outputformat,
            "filters":args.filters,
            "cachepos":args.cachepos
        }

    else:
        philter_config = {
            "verbose":args.verbose,
            "run_eval":args.run_eval,
            "freq_table":args.freq_table,
            "initials":args.initials,
            "finpath":args.input,
            "foutpath":args.output,
            "outformat":args.outputformat,
            "ucsfformat":args.ucsfformat,
            "anno_folder":args.anno,
            "filters":args.filters,
            "xml":args.xml,
            "coords":args.coords,
            "eval_out":args.eval_output,
            "cachepos":args.cachepos
        }
   
    if verbose:
        print("RUNNING ", philter_config['filters'])


    filterer = Philter(philter_config)

    #map any sets, pos and regex groups we have in our config
    filterer.map_coordinates()

    
    #transform the data 
    #Priority order is maintained in the pattern list
    filterer.transform()

    if args.pdf_output:
        if args.outputformat != "asterisk":
            print("Skipping PDF export: --pdf_output expects --outputformat asterisk (text output).")
        else:
            try:
                converted_count = _export_output_txts_to_pdf(args.output)
                print(f"PDF export complete. Created {converted_count} PDF file(s) in {args.output}")
            except Exception as exc:
                print(f"PDF export failed: {exc}")

    #evaluate the effectiveness
    if run_eval and args.outputformat == "asterisk":
        filterer.eval(
            philter_config,
            in_path=args.output,
            anno_path=args.anno,
            anno_suffix=".txt",
            fn_output = "data/phi/fn.txt",
            fp_output = "data/phi/fp.txt",
            summary_output="./data/phi/summary.json",
            phi_matcher=re.compile("\*+"),
            pre_process=r":|\,|\-|\/|_|~", #characters we're going to strip from our notes to analyze against anno
            only_digits=False,
            pre_process2= r"[^a-zA-Z0-9]",
            punctuation_matcher=re.compile(r"[^a-zA-Z0-9\*]"))

# error analysis
        
if __name__ == "__main__":
    main()
