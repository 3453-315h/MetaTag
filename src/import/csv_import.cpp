#include "csv_import.h"
#include "track.h"
#include <QFile>
#include <QTextStream>
#include <QDebug>
#include <QStringList>
#include <QUrl>

namespace metatag {

static QStringList parseCsvLine(const QString& line)
{
    QStringList fields;
    QString field;
    bool inQuotes = false;
    bool fieldHasQuotes = false;

    for (int i = 0; i < line.length(); ++i) {
        QChar ch = line[i];
        if (ch == '"') {
            if (inQuotes && i + 1 < line.length() && line[i + 1] == '"') {
                // Escaped quote: ""
                field += '"';
                ++i; // Skip next quote
                fieldHasQuotes = true;
            } else {
                // Toggle quote state
                inQuotes = !inQuotes;
                fieldHasQuotes = true;
            }
        } else if (ch == ',' && !inQuotes) {
            // End of field
            if (fieldHasQuotes) {
                // Remove surrounding quotes if present
                if (field.startsWith('"') && field.endsWith('"')) {
                    field = field.mid(1, field.length() - 2);
                }
            }
            fields.append(field);
            field.clear();
            fieldHasQuotes = false;
        } else {
            field += ch;
        }
    }

    // Add the last field
    if (fieldHasQuotes) {
        if (field.startsWith('"') && field.endsWith('"')) {
            field = field.mid(1, field.length() - 2);
        }
    }
    fields.append(field);

    return fields;
}

bool CsvImport::import(const QString& csvPath, QVector<Track>& tracks)
{
    QFile file(csvPath);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
        qWarning() << "Failed to open CSV file:" << csvPath;
        return false;
    }
    
    QTextStream stream(&file);
    stream.setCodec("UTF-8");
    
    // Read header
    if (stream.atEnd())
        return false;
    QString headerLine = stream.readLine();
    QStringList headers = parseCsvLine(headerLine);
    
    // Map header indices to field types
    QVector<int> artistIdx, albumIdx, titleIdx, trackNumIdx, discNumIdx, genreIdx,
                 yearIdx, commentIdx, composerIdx, groupingIdx, bpmIdx, filePathIdx;
    
    for (int i = 0; i < headers.size(); ++i) {
        QString h = headers[i].toLower().trimmed();
        if (h == "artist" || h == "artist name")
            artistIdx.append(i);
        else if (h == "album" || h == "album title")
            albumIdx.append(i);
        else if (h == "title" || h == "track title")
            titleIdx.append(i);
        else if (h == "track" || h == "track number")
            trackNumIdx.append(i);
        else if (h == "disc" || h == "disc number")
            discNumIdx.append(i);
        else if (h == "genre")
            genreIdx.append(i);
        else if (h == "year")
            yearIdx.append(i);
        else if (h == "comment")
            commentIdx.append(i);
        else if (h == "composer")
            composerIdx.append(i);
        else if (h == "grouping")
            groupingIdx.append(i);
        else if (h == "bpm")
            bpmIdx.append(i);
        else if (h == "file" || h == "file path" || h == "path")
            filePathIdx.append(i);
    }
    
    if (filePathIdx.isEmpty()) {
        qWarning() << "CSV missing file path column";
        return false;
    }
    
    // Read data rows
    while (!stream.atEnd()) {
        QString line = stream.readLine().trimmed();
        if (line.isEmpty())
            continue;

        QStringList fields = parseCsvLine(line);
        if (fields.size() != headers.size()) {
            qWarning() << "CSV line" << (tracks.size() + 1) << "has" << fields.size()
                      << "fields but expected" << headers.size() << ", skipping";
            continue;
        }

        // Use first file path column
        QString filePath = fields[filePathIdx.first()].trimmed();
        if (filePath.isEmpty()) {
            qWarning() << "CSV line" << (tracks.size() + 1) << "has empty file path, skipping";
            continue;
        }

        // Check if file exists
        if (!QFile::exists(filePath)) {
            qWarning() << "CSV file does not exist:" << filePath << ", skipping";
            continue;
        }

        Track track(filePath);
        if (!track.load()) {
            qWarning() << "Failed to load track:" << filePath << ", skipping";
            continue;
        }
        
        // Apply metadata from CSV
        if (!artistIdx.isEmpty())
            track.setArtist(fields[artistIdx.first()].trimmed());
        if (!albumIdx.isEmpty())
            track.setAlbum(fields[albumIdx.first()].trimmed());
        if (!titleIdx.isEmpty())
            track.setTitle(fields[titleIdx.first()].trimmed());
        if (!trackNumIdx.isEmpty())
            track.setTrackNumber(fields[trackNumIdx.first()].toInt());
        if (!discNumIdx.isEmpty())
            track.setDiscNumber(fields[discNumIdx.first()].toInt());
        if (!genreIdx.isEmpty())
            track.setGenre(fields[genreIdx.first()].trimmed());
        if (!yearIdx.isEmpty())
            track.setYear(fields[yearIdx.first()].toInt());
        if (!commentIdx.isEmpty())
            track.setComment(fields[commentIdx.first()].trimmed());
        if (!composerIdx.isEmpty())
            track.setComposer(fields[composerIdx.first()].trimmed());
        if (!groupingIdx.isEmpty())
            track.setGrouping(fields[groupingIdx.first()].trimmed());
        if (!bpmIdx.isEmpty())
            track.setBpm(fields[bpmIdx.first()].toInt());
        
        tracks.append(track);
    }
    
    file.close();
    return true;
}

}