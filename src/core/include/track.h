#pragma once

#include <QString>
#include <QVector>
#include <QImage>

namespace metatag {

class Track {
public:
    Track() = default;
    explicit Track(const QString& filePath);

    bool load();
    bool save();

    QString filePath() const { return m_filePath; }
    QString artist() const { return m_artist; }
    QString album() const { return m_album; }
    QString title() const { return m_title; }
    int trackNumber() const { return m_trackNumber; }
    int discNumber() const { return m_discNumber; }
    QString genre() const { return m_genre; }
    int year() const { return m_year; }
    QString comment() const { return m_comment; }
    QString composer() const { return m_composer; }
    QString grouping() const { return m_grouping; }
    int bpm() const { return m_bpm; }
    QImage coverArt() const { return m_coverArt; }
    int duration() const { return m_duration; }
    bool isLoaded() const { return m_loaded; }
    bool isDirty() const { return m_dirty; }
    void setDirty(bool dirty = true) { m_dirty = dirty; }

    void setArtist(const QString& artist) { m_artist = artist; m_dirty = true; }
    void setAlbum(const QString& album) { m_album = album; m_dirty = true; }
    void setTitle(const QString& title) { m_title = title; m_dirty = true; }
    void setTrackNumber(int number) { m_trackNumber = number; m_dirty = true; }
    void setDiscNumber(int number) { m_discNumber = number; m_dirty = true; }
    void setGenre(const QString& genre) { m_genre = genre; m_dirty = true; }
    void setYear(int year) { m_year = year; m_dirty = true; }
    void setComment(const QString& comment) { m_comment = comment; m_dirty = true; }
    void setComposer(const QString& composer) { m_composer = composer; m_dirty = true; }
    void setGrouping(const QString& grouping) { m_grouping = grouping; m_dirty = true; }
    void setBpm(int bpm) { m_bpm = bpm; m_dirty = true; }
    void setCoverArt(const QImage& cover) { m_coverArt = cover; m_dirty = true; }
    void setDuration(int ms) { m_duration = ms; }

private:
    bool saveCoverArt(TagLib::FileRef& file, const QByteArray& imageData);
    bool loadCoverArt(TagLib::FileRef& file);

    QString m_filePath;
    QString m_artist;
    QString m_album;
    QString m_title;
    int m_trackNumber = 0;
    int m_discNumber = 0;
    QString m_genre;
    int m_year = 0;
    QString m_comment;
    QString m_composer;
    QString m_grouping;
    int m_bpm = 0;
    QImage m_coverArt;
    int m_duration = 0;
    bool m_loaded = false;
    bool m_dirty = false;
};

}