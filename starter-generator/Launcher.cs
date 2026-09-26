// Vorlage fuer die Start-EXE eines Projekts.
// Wird von Starter-erstellen.ps1 mit dem in Windows eingebauten
// C#-Compiler (csc.exe, .NET Framework 4) uebersetzt. Deshalb nur
// C#-5-Sprachmittel verwenden (keine $"..."-Strings, kein ?. usw.).
//
// Alle Pfade werden zur Laufzeit relativ zum Ordner der EXE aufgeloest,
// damit ein Projektordner samt EXE beliebig verschoben/kopiert werden kann.

using System;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Security.Cryptography;
using System.Text;

internal static class Launcher
{
    // Von Starter-erstellen.ps1 ersetzt.
    private const string Mode = "@@MODE@@";       // ps1 | bat | npm | python | streamlit | module | entry | open
    private const string Target = "@@TARGET@@";   // Datei, npm-Skript, Python-Modul bzw. "modul:funktion"
    private const string Title = "@@TITLE@@";     // Anzeigename des Projekts
    private const string Setup = "@@SETUP@@";     // Python-Umgebung: none | repair | full
    private const string AskFile = "@@ASKFILE@@"; // "1": ohne Argument nach einer Datei fragen

    [STAThread]
    private static int Main(string[] args)
    {
        string baseDir = AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\', '/');
        Directory.SetCurrentDirectory(baseDir);

        if (Mode == "open")
        {
            return OpenWithDefaultApp(Path.Combine(baseDir, Target));
        }

        try { Console.Title = Title; } catch (IOException) { }

        // Strg+C soll nur das gestartete Programm beenden, nicht den Starter,
        // damit eine Fehlermeldung danach noch lesbar bleibt.
        Console.CancelKeyPress += delegate(object sender, ConsoleCancelEventArgs e) { e.Cancel = true; };

        // Programme, die eine Datei erwarten (Datei auf die EXE ziehen):
        // ohne Datei einen Auswahldialog zeigen.
        if (AskFile == "1" && args.Length == 0)
        {
            string file = AskForFile();
            if (file == null) return 0;
            args = new string[] { file };
        }

        if (Setup != "none" && !PreparePythonEnv(baseDir))
        {
            return Fail(1);
        }

        string fileName;
        string arguments;
        if (!BuildCommand(baseDir, args, out fileName, out arguments))
        {
            return Fail(1);
        }

        var psi = new ProcessStartInfo(fileName, arguments);
        psi.UseShellExecute = false;
        psi.WorkingDirectory = baseDir;
        // Verhindert MSBuild-Abstuerze (MSB4166) bei dotnet-Projekten.
        psi.EnvironmentVariables["MSBUILDDISABLENODEREUSE"] = "1";
        if (Mode == "module" || Mode == "entry")
        {
            string old = psi.EnvironmentVariables["PYTHONPATH"];
            psi.EnvironmentVariables["PYTHONPATH"] = baseDir + ";" + Path.Combine(baseDir, "src")
                + (string.IsNullOrEmpty(old) ? "" : ";" + old);
        }

        int exitCode;
        try
        {
            using (Process p = Process.Start(psi))
            {
                p.WaitForExit();
                exitCode = p.ExitCode;
            }
        }
        catch (Win32Exception ex)
        {
            Console.WriteLine();
            Console.WriteLine("Konnte \"" + fileName + "\" nicht starten: " + ex.Message);
            Console.WriteLine(MissingToolHint());
            return Fail(1);
        }

        if (exitCode != 0)
        {
            Console.WriteLine();
            Console.WriteLine("Das Programm wurde mit Fehlercode " + exitCode + " beendet.");
            return Fail(exitCode);
        }
        return 0;
    }

    private static bool BuildCommand(string baseDir, string[] args, out string fileName, out string arguments)
    {
        // Auf die EXE gezogene Dateien werden an das Programm weitergereicht.
        string extra = "";
        foreach (string a in args) extra += " " + Quote(a);

        string target = Path.Combine(baseDir, Target);
        fileName = null;
        arguments = null;

        switch (Mode)
        {
            case "ps1":
                fileName = "powershell.exe";
                arguments = "-NoProfile -ExecutionPolicy Bypass -File " + Quote(target) + extra;
                return true;

            case "bat":
                fileName = "cmd.exe";
                // Aeussere Anfuehrungszeichen werden von cmd /c entfernt.
                arguments = "/c \"" + Quote(target) + extra + "\"";
                return true;

            case "npm":
                fileName = "cmd.exe";
                string run = Target == "start" ? "npm start" : "npm run " + Target;
                if (!Directory.Exists(Path.Combine(baseDir, "node_modules")))
                {
                    Console.WriteLine("Erster Start: installiere Abhaengigkeiten (npm install) ...");
                    run = "npm install && " + run;
                }
                arguments = "/c " + run;
                return true;

            case "python":
            case "streamlit":
            case "module":
            case "entry":
                string python = FindPython(baseDir, true);
                if (python == null)
                {
                    Console.WriteLine("Python wurde nicht gefunden.");
                    Console.WriteLine(MissingToolHint());
                    return false;
                }
                fileName = python;
                if (Mode == "module")
                {
                    arguments = "-m " + Target + extra;
                }
                else if (Mode == "entry")
                {
                    string[] parts = Target.Split(':');
                    arguments = "-c \"import sys; from " + parts[0] + " import " + parts[1]
                        + "; sys.exit(" + parts[1] + "())\"" + extra;
                }
                else
                {
                    arguments = Mode == "streamlit"
                        ? "-m streamlit run " + Quote(target) + (extra.Length > 0 ? " --" + extra : "")
                        : Quote(target) + extra;
                }
                return true;
        }

        Console.WriteLine("Unbekannter Startmodus: " + Mode);
        return false;
    }

    // Bevorzugt (wenn erlaubt) eine projekteigene virtuelle Umgebung, sonst Python aus dem PATH.
    private static string FindPython(string baseDir, bool allowVenv)
    {
        string venvDir = allowVenv ? FindVenvDir(baseDir) : null;
        if (venvDir != null)
        {
            string candidate = Path.Combine(venvDir, "Scripts", "python.exe");
            if (File.Exists(candidate)) return candidate;
        }
        string[] names = { "python.exe", "py.exe" };
        foreach (string name in names)
        {
            string found = FindOnPath(name);
            // Der Microsoft-Store-Platzhalter unter WindowsApps ist kein echtes Python.
            if (found != null && found.IndexOf("WindowsApps", StringComparison.OrdinalIgnoreCase) < 0)
                return found;
        }
        return null;
    }

    private static string FindVenvDir(string baseDir)
    {
        string[] venvs = { ".venv", "venv", "env" };
        foreach (string venv in venvs)
        {
            string dir = Path.Combine(baseDir, venv);
            if (File.Exists(Path.Combine(dir, "pyvenv.cfg"))) return dir;
        }
        return null;
    }

    // Eine virtuelle Umgebung merkt sich den Pfad des Python, mit dem sie
    // erstellt wurde. Gibt es das dort nicht mehr (anderer Rechner, anderer
    // Benutzer, Python neu installiert), ist sie unbrauchbar.
    private static bool IsVenvBroken(string venvDir)
    {
        if (!File.Exists(Path.Combine(venvDir, "Scripts", "python.exe"))) return true;
        foreach (string line in File.ReadAllLines(Path.Combine(venvDir, "pyvenv.cfg")))
        {
            int eq = line.IndexOf('=');
            if (eq > 0 && line.Substring(0, eq).Trim().Equals("home", StringComparison.OrdinalIgnoreCase))
            {
                return !File.Exists(Path.Combine(line.Substring(eq + 1).Trim(), "python.exe"));
            }
        }
        return false;
    }

    // Setup "repair": defekte Umgebung loeschen, das Projektskript legt sie neu an.
    // Setup "full":   Umgebung bei Bedarf anlegen/reparieren und Abhaengigkeiten
    //                 installieren (erneut, sobald sich requirements.txt/pyproject.toml aendern).
    private static bool PreparePythonEnv(string baseDir)
    {
        string venvDir = FindVenvDir(baseDir);
        bool broken = venvDir != null && IsVenvBroken(venvDir);
        if (broken)
        {
            Console.WriteLine("Die Python-Umgebung \"" + Path.GetFileName(venvDir) + "\" ist defekt (sie wurde mit einem");
            Console.WriteLine("Python erstellt, das es auf diesem Rechner nicht gibt). Sie wird neu angelegt ...");
        }
        if (Setup == "repair")
        {
            if (!broken) return true;
            try { Directory.Delete(venvDir, true); return true; }
            catch (Exception ex)
            {
                Console.WriteLine("Konnte \"" + venvDir + "\" nicht loeschen: " + ex.Message);
                Console.WriteLine("Bitte den Ordner von Hand loeschen und erneut starten.");
                return false;
            }
        }

        string requirements = Path.Combine(baseDir, "requirements.txt");
        string pyproject = Path.Combine(baseDir, "pyproject.toml");
        bool hasReq = File.Exists(requirements);
        bool hasPyproject = File.Exists(pyproject);

        if (venvDir == null || broken)
        {
            if (venvDir == null)
            {
                venvDir = Path.Combine(baseDir, ".venv");
                Console.WriteLine("Erster Start: richte die Python-Umgebung ein (kann einige Minuten dauern) ...");
            }
            string systemPython = FindPython(baseDir, false);
            if (systemPython == null)
            {
                Console.WriteLine("Python wurde nicht gefunden.");
                Console.WriteLine(MissingToolHint());
                return false;
            }
            if (!Run(systemPython, "-m venv --clear " + Quote(venvDir), baseDir))
            {
                Console.WriteLine("Die Python-Umgebung konnte nicht angelegt werden.");
                return false;
            }
        }

        string python = Path.Combine(venvDir, "Scripts", "python.exe");
        string marker = Path.Combine(venvDir, "starter-installiert.txt");
        string hash = HashFiles(requirements, pyproject);
        if (File.Exists(marker) && File.ReadAllText(marker).Trim() == hash) return true;

        Console.WriteLine("Installiere die benoetigten Python-Pakete ...");
        bool ok = true;
        if (hasReq)
        {
            ok = Run(python, "-m pip install -r requirements.txt", baseDir);
        }
        else if (hasPyproject)
        {
            ok = Run(python, "-m pip install -e .", baseDir);
        }
        if (!ok)
        {
            Console.WriteLine("Die Installation der Python-Pakete ist fehlgeschlagen (siehe oben).");
            return false;
        }
        string deps = (hasReq ? File.ReadAllText(requirements) : "") + (hasPyproject ? File.ReadAllText(pyproject) : "");
        if (deps.IndexOf("playwright", StringComparison.OrdinalIgnoreCase) >= 0)
        {
            Console.WriteLine("Installiere den Browser fuer Playwright ...");
            Run(python, "-m playwright install chromium", baseDir);
        }
        File.WriteAllText(marker, hash);
        Console.WriteLine();
        return true;
    }

    private static string HashFiles(params string[] files)
    {
        using (SHA1 sha = SHA1.Create())
        {
            var all = new MemoryStream();
            foreach (string f in files)
            {
                if (!File.Exists(f)) continue;
                byte[] data = File.ReadAllBytes(f);
                all.Write(data, 0, data.Length);
            }
            return BitConverter.ToString(sha.ComputeHash(all.ToArray())).Replace("-", "");
        }
    }

    private static bool Run(string fileName, string arguments, string workDir)
    {
        var psi = new ProcessStartInfo(fileName, arguments);
        psi.UseShellExecute = false;
        psi.WorkingDirectory = workDir;
        try
        {
            using (Process p = Process.Start(psi))
            {
                p.WaitForExit();
                return p.ExitCode == 0;
            }
        }
        catch (Win32Exception ex)
        {
            Console.WriteLine("Konnte \"" + fileName + "\" nicht starten: " + ex.Message);
            return false;
        }
    }

    private static string FindOnPath(string exe)
    {
        string path = Environment.GetEnvironmentVariable("PATH") ?? "";
        foreach (string dir in path.Split(';'))
        {
            if (dir.Trim().Length == 0) continue;
            try
            {
                string candidate = Path.Combine(dir.Trim().Trim('"'), exe);
                if (File.Exists(candidate)) return candidate;
            }
            catch (ArgumentException) { }
        }
        return null;
    }

    private static int OpenWithDefaultApp(string target)
    {
        try
        {
            var psi = new ProcessStartInfo(target);
            psi.UseShellExecute = true;
            psi.WorkingDirectory = Path.GetDirectoryName(target);
            Process.Start(psi);
            return 0;
        }
        catch (Exception ex)
        {
            System.Windows.Forms.MessageBox.Show(
                "Konnte \"" + target + "\" nicht oeffnen:\n" + ex.Message, Title);
            return 1;
        }
    }

    private static string AskForFile()
    {
        using (var dialog = new System.Windows.Forms.OpenFileDialog())
        {
            dialog.Title = Title + " - Datei auswaehlen";
            dialog.Filter = "Alle Dateien (*.*)|*.*";
            if (dialog.ShowDialog() != System.Windows.Forms.DialogResult.OK) return null;
            return dialog.FileName;
        }
    }

    private static string MissingToolHint()
    {
        switch (Mode)
        {
            case "npm": return "Bitte Node.js installieren: https://nodejs.org/";
            case "python":
            case "streamlit":
            case "module":
            case "entry": return "Bitte Python installieren (https://www.python.org/downloads/) und beim Setup \"Add python.exe to PATH\" aktivieren.";
            default: return "";
        }
    }

    private static string Quote(string s)
    {
        return "\"" + s + "\"";
    }

    private static int Fail(int code)
    {
        Console.WriteLine();
        Console.WriteLine("Zum Schliessen eine beliebige Taste druecken ...");
        try { Console.ReadKey(true); } catch (InvalidOperationException) { }
        return code;
    }
}
