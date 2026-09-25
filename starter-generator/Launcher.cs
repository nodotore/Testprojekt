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

internal static class Launcher
{
    // Von Starter-erstellen.ps1 ersetzt.
    private const string Mode = "@@MODE@@";       // ps1 | bat | npm | python | streamlit | open
    private const string Target = "@@TARGET@@";   // Datei bzw. npm-Skriptname, relativ zum EXE-Ordner
    private const string Title = "@@TITLE@@";     // Anzeigename des Projekts

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

        string fileName;
        string arguments;
        if (!BuildCommand(baseDir, out fileName, out arguments))
        {
            return Fail(1);
        }

        var psi = new ProcessStartInfo(fileName, arguments);
        psi.UseShellExecute = false;
        psi.WorkingDirectory = baseDir;

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

    private static bool BuildCommand(string baseDir, out string fileName, out string arguments)
    {
        string target = Path.Combine(baseDir, Target);
        fileName = null;
        arguments = null;

        switch (Mode)
        {
            case "ps1":
                fileName = "powershell.exe";
                arguments = "-NoProfile -ExecutionPolicy Bypass -File " + Quote(target);
                return true;

            case "bat":
                fileName = "cmd.exe";
                // Aeussere Anfuehrungszeichen werden von cmd /c entfernt.
                arguments = "/c \"" + Quote(target) + "\"";
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
                string python = FindPython(baseDir);
                if (python == null)
                {
                    Console.WriteLine("Python wurde nicht gefunden.");
                    Console.WriteLine(MissingToolHint());
                    return false;
                }
                fileName = python;
                arguments = (Mode == "streamlit" ? "-m streamlit run " : "") + Quote(target);
                return true;
        }

        Console.WriteLine("Unbekannter Startmodus: " + Mode);
        return false;
    }

    // Bevorzugt eine projekteigene virtuelle Umgebung, sonst Python aus dem PATH.
    private static string FindPython(string baseDir)
    {
        string[] venvs = { ".venv", "venv", "env" };
        foreach (string venv in venvs)
        {
            string candidate = Path.Combine(baseDir, venv, "Scripts", "python.exe");
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

    private static string MissingToolHint()
    {
        switch (Mode)
        {
            case "npm": return "Bitte Node.js installieren: https://nodejs.org/";
            case "python":
            case "streamlit": return "Bitte Python installieren (https://www.python.org/downloads/) und beim Setup \"Add python.exe to PATH\" aktivieren.";
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
