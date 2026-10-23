#include "csv_import.h"
#include "track.h"
#include <QFile>
#include <QTextStream>
#include <QDebug>
#include <QStringList>
#include <QUrl>

namespace metatag {

static QVector<QStringList> parseCsvContent(const QString& content)
{
    QVector<QStringList> records;
    QStringList currentRecord;
    QString currentField;
    bool inQuotes = false;
    int len = content.length();

    for (int i = 0; i < len; ++i) {
        QChar ch = content[i];

        if (inQuotes) {
            if (ch == '"') {
                if (i + 1 < len && content[i + 1] == '"') {
                    currentField += '"';
                    ++i; // skip escaped quote
                } else {
                    inQuotes = false;
                }
            } else {
                currentField += ch;
            }
        } else {
            if (ch == '"') {
                inQuotes = true;
            } else if (ch == ',') {
                currentRecord.append(currentField);
                currentField.clear();
            } else if (ch == '\n') {
                currentRecord.append(currentField);
                currentField.clear();
                records.append(currentRecord);
                currentRecord.clear();
            } else if (ch == '\r') {
                if (i + 1 < len && content[i + 1] == '\n') {
                    ++i; // skip \n in \r\n
                }
                currentRecord.append(currentField);
                currentField.clear();
                records.append(currentRecord);
                currentRecord.clear();
            } else {
                currentField += ch;
            }
        }
    }

    if (!currentField.isEmpty() || !currentRecord.isEmpty()) {
        currentRecord.append(currentField);
        records.append(currentRecord);
    }

    return records;
}

bool CsvImport::import(const QString& csvPath, QVector<Track>& tracks)
{
    QFile file(csvPath);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
        qWarning() << "Failed to open CSV file:" << csvPath;
        return false;
    }

    QTextStream stream(&file);
#if QT_VERSION < QT_VERSION_CHECK(6, 0, 0)
    stream.setCodec("UTF-8");
#else
    stream.setEncoding(QStringConverter::Utf8);
#endif

    QString content = stream.readAll();
    file.close();

    QVector<QStringList> records = parseCsvContent(content);
    if (records.isEmpty())
        return false;

    QStringList headers = records.first();

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

    for (int r = 1; r < records.size(); ++r) {
        const QStringList& fields = records[r];
        if (fields.isEmpty() || (fields.size() == 1 && fields[0].trimmed().isEmpty()))
            continue;

        if (fields.size() != headers.size()) {
            qWarning() << "CSV line" << (r + 1) << "has" << fields.size()
                       << "fields but expected" << headers.size() << ", skipping";
            continue;
        }

        QString filePath = fields[filePathIdx.first()].trimmed();
        if (filePath.isEmpty()) {
            qWarning() << "CSV line" << (r + 1) << "has empty file path, skipping";
            continue;
        }

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

    return true;
}

} // namespace metatag