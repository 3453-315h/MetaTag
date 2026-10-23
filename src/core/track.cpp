#include "track.h"
#include <taglib/taglib.h>
#include <taglib/fileref.h>
#include <taglib/tag.h>
#include <taglib/tpropertymap.h>
#include <taglib/attachedpictureframe.h>
#include <taglib/id3v2tag.h>
#include <taglib/mpegfile.h>
#include <taglib/flacfile.h>
#include <taglib/mp4file.h>
#include <taglib/vorbisfile.h>
#include <taglib/wavfile.h>
#include <taglib/aifffile.h>
#include <taglib/flacpicture.h>
#include <taglib/mp4coverart.h>
#include <taglib/mp4item.h>
#include <taglib/oggfile.h>
#include <taglib/opusfile.h>
#include <taglib/xiphcomment.h>

#include <QImage>
#include <QBuffer>
#include <QDebug>

namespace metatag {

Track::Track(const QString& filePath)
    : m_filePath(filePath)
{
}

bool Track::load()
{
    m_loaded = false;
    TagLib::FileRef file(m_filePath.toStdString().c_str());
    if (file.isNull() || !file.file() || !file.file()->isValid() || !file.tag() || 
        !file.audioProperties() || file.audioProperties()->channels() <= 0)
        return false;

    TagLib::Tag *tag = file.tag();
    m_artist = QString::fromUtf8(tag->artist().toCString(true));
    m_album = QString::fromUtf8(tag->album().toCString(true));
    m_title = QString::fromUtf8(tag->title().toCString(true));
    m_trackNumber = tag->track();
    m_genre = QString::fromUtf8(tag->genre().toCString(true));
    m_year = tag->year();
    m_comment = QString::fromUtf8(tag->comment().toCString(true));

    // Extract additional fields from property map
    TagLib::PropertyMap props = file.file()->properties();
    if (props.contains("COMPOSER") && !props["COMPOSER"].isEmpty()) {
        m_composer = QString::fromUtf8(props["COMPOSER"].front().toCString(true));
    }
    if (props.contains("GROUPING") && !props["GROUPING"].isEmpty()) {
        m_grouping = QString::fromUtf8(props["GROUPING"].front().toCString(true));
    }
    if (props.contains("BPM") && !props["BPM"].isEmpty()) {
        m_bpm = props["BPM"].front().toInt();
    }
    if (props.contains("DISCNUMBER") && !props["DISCNUMBER"].isEmpty()) {
        m_discNumber = props["DISCNUMBER"].front().toInt();
    }

    // Try to extract cover art
    loadCoverArt(file);

    // Duration
    if (file.audioProperties()) {
        m_duration = file.audioProperties()->lengthInMilliseconds();
    }

    m_dirty = false;
    m_coverArtModified = false;
    m_modifiedFields.clear();
    m_loaded = true;
    return true;
}

bool Track::loadCoverArt(TagLib::FileRef& file)
{
    // MP3/ID3v2: prefer FrontCover
    if (TagLib::MPEG::File *mpegFile = dynamic_cast<TagLib::MPEG::File*>(file.file())) {
        if (mpegFile->ID3v2Tag()) {
            auto frames = mpegFile->ID3v2Tag()->frameList("APIC");
            if (!frames.isEmpty()) {
                TagLib::ID3v2::AttachedPictureFrame *frontPic = nullptr;
                for (auto *f : frames) {
                    auto *p = dynamic_cast<TagLib::ID3v2::AttachedPictureFrame*>(f);
                    if (p && p->type() == TagLib::ID3v2::AttachedPictureFrame::FrontCover) {
                        frontPic = p;
                        break;
                    }
                }
                if (!frontPic) {
                    frontPic = dynamic_cast<TagLib::ID3v2::AttachedPictureFrame*>(frames.front());
                }
                if (frontPic) {
                    QByteArray data(frontPic->picture().data(), frontPic->picture().size());
                    return m_coverArt.loadFromData(data);
                }
            }
        }
        return false;
    }

    // FLAC: prefer FrontCover
    if (TagLib::FLAC::File *flacFile = dynamic_cast<TagLib::FLAC::File*>(file.file())) {
        auto pictureList = flacFile->pictureList();
        if (!pictureList.isEmpty()) {
            TagLib::FLAC::Picture *frontPic = nullptr;
            for (auto *pic : pictureList) {
                if (pic && pic->type() == TagLib::FLAC::Picture::FrontCover) {
                    frontPic = pic;
                    break;
                }
            }
            if (!frontPic) {
                frontPic = pictureList.front();
            }
            if (frontPic) {
                QByteArray data(frontPic->data().data(), frontPic->data().size());
                return m_coverArt.loadFromData(data);
            }
        }
        return false;
    }

    // MP4
    if (TagLib::MP4::File *mp4File = dynamic_cast<TagLib::MP4::File*>(file.file())) {
        if (mp4File->tag()) {
#if TAGLIB_MAJOR_VERSION >= 2
            auto items = mp4File->tag()->itemMap();
            if (items.contains("covr")) {
                auto coverList = items["covr"].toCoverArtList();
                if (!coverList.isEmpty()) {
                    TagLib::MP4::CoverArt cover = coverList.front();
                    QByteArray data(cover.data().data(), cover.data().size());
                    return m_coverArt.loadFromData(data);
                }
            }
#else
            auto coverList = mp4File->tag()->itemListMap()["covr"].toCoverArtList();
            if (!coverList.isEmpty()) {
                TagLib::MP4::CoverArt cover = coverList.front();
                QByteArray data(cover.data().data(), cover.data().size());
                return m_coverArt.loadFromData(data);
            }
#endif
        }
        return false;
    }

    // Ogg Vorbis: prefer FrontCover
    if (TagLib::Ogg::Vorbis::File *vorbisFile = dynamic_cast<TagLib::Ogg::Vorbis::File*>(file.file())) {
        if (vorbisFile->tag()) {
            auto pictures = vorbisFile->tag()->pictureList();
            if (!pictures.isEmpty()) {
                TagLib::FLAC::Picture *frontPic = nullptr;
                for (auto *pic : pictures) {
                    if (pic && pic->type() == TagLib::FLAC::Picture::FrontCover) {
                        frontPic = pic;
                        break;
                    }
                }
                if (!frontPic) {
                    frontPic = pictures.front();
                }
                if (frontPic) {
                    QByteArray data(frontPic->data().data(), frontPic->data().size());
                    return m_coverArt.loadFromData(data);
                }
            }
        }
        return false;
    }

    // Ogg Opus: prefer FrontCover
    if (TagLib::Ogg::Opus::File *opusFile = dynamic_cast<TagLib::Ogg::Opus::File*>(file.file())) {
        if (opusFile->tag()) {
            auto pictures = opusFile->tag()->pictureList();
            if (!pictures.isEmpty()) {
                TagLib::FLAC::Picture *frontPic = nullptr;
                for (auto *pic : pictures) {
                    if (pic && pic->type() == TagLib::FLAC::Picture::FrontCover) {
                        frontPic = pic;
                        break;
                    }
                }
                if (!frontPic) {
                    frontPic = pictures.front();
                }
                if (frontPic) {
                    QByteArray data(frontPic->data().data(), frontPic->data().size());
                    return m_coverArt.loadFromData(data);
                }
            }
        }
        return false;
    }

    return false;
}

bool Track::save()
{
    TagLib::FileRef file(m_filePath.toStdString().c_str(), true, TagLib::AudioProperties::Fast);
    if (file.isNull() || !file.file() || !file.file()->isValid() || !file.tag() || 
        !file.audioProperties() || file.audioProperties()->channels() <= 0)
        return false;

    bool all = m_modifiedFields.isEmpty();
    TagLib::Tag *tag = file.tag();
    if (all || m_modifiedFields.contains("artist"))
        tag->setArtist(TagLib::String(m_artist.toUtf8().constData(), TagLib::String::UTF8));
    if (all || m_modifiedFields.contains("album"))
        tag->setAlbum(TagLib::String(m_album.toUtf8().constData(), TagLib::String::UTF8));
    if (all || m_modifiedFields.contains("title"))
        tag->setTitle(TagLib::String(m_title.toUtf8().constData(), TagLib::String::UTF8));
    if (all || m_modifiedFields.contains("trackNumber"))
        tag->setTrack(m_trackNumber);
    if (all || m_modifiedFields.contains("genre"))
        tag->setGenre(TagLib::String(m_genre.toUtf8().constData(), TagLib::String::UTF8));
    if (all || m_modifiedFields.contains("year"))
        tag->setYear(m_year);
    if (all || m_modifiedFields.contains("comment"))
        tag->setComment(TagLib::String(m_comment.toUtf8().constData(), TagLib::String::UTF8));

    // Update property map with additional fields only if modified or saving all
    TagLib::PropertyMap props = file.file()->properties();
    if (all || m_modifiedFields.contains("composer")) {
        if (!m_composer.isEmpty()) {
            props["COMPOSER"] = TagLib::StringList(TagLib::String(m_composer.toUtf8().constData(), TagLib::String::UTF8));
        } else {
            props.erase("COMPOSER");
        }
    }
    if (all || m_modifiedFields.contains("grouping")) {
        if (!m_grouping.isEmpty()) {
            props["GROUPING"] = TagLib::StringList(TagLib::String(m_grouping.toUtf8().constData(), TagLib::String::UTF8));
        } else {
            props.erase("GROUPING");
        }
    }
    if (all || m_modifiedFields.contains("bpm")) {
        if (m_bpm > 0) {
            props["BPM"] = TagLib::StringList(TagLib::String(QString::number(m_bpm).toUtf8().constData(), TagLib::String::UTF8));
        } else {
            props.erase("BPM");
        }
    }
    if (all || m_modifiedFields.contains("discNumber")) {
        if (m_discNumber > 0) {
            props["DISCNUMBER"] = TagLib::StringList(TagLib::String(QString::number(m_discNumber).toUtf8().constData(), TagLib::String::UTF8));
        } else {
            props.erase("DISCNUMBER");
        }
    }
    file.file()->setProperties(props);

    // Save or remove cover art if modified
    if (m_coverArtModified) {
        if (!m_coverArt.isNull()) {
            QByteArray bytes;
            QBuffer buffer(&bytes);
            buffer.open(QIODevice::WriteOnly);
            if (m_coverArt.save(&buffer, "PNG")) { // Use PNG for lossless
                if (!saveCoverArt(file, bytes)) {
                    qWarning() << "Failed to save cover art";
                    return false;
                }
            } else {
                qWarning() << "Failed to encode cover art as PNG";
                return false;
            }
        } else {
            if (!removeCoverArt(file)) {
                qWarning() << "Failed to remove cover art";
                return false;
            }
        }
    }

    bool ok = file.save();
    if (ok) {
        m_dirty = false;
        m_coverArtModified = false;
        m_modifiedFields.clear();
    }
    return ok;
}

bool Track::removeCoverArt(TagLib::FileRef& file)
{
    // MP3/ID3v2: remove only FrontCover frames, preserving other picture types
    if (TagLib::MPEG::File *mpegFile = dynamic_cast<TagLib::MPEG::File*>(file.file())) {
        if (auto *id3v2Tag = mpegFile->ID3v2Tag(false)) {
            auto frames = id3v2Tag->frameList("APIC");
            for (auto *f : frames) {
                if (auto *picFrame = dynamic_cast<TagLib::ID3v2::AttachedPictureFrame*>(f)) {
                    if (picFrame->type() == TagLib::ID3v2::AttachedPictureFrame::FrontCover) {
                        id3v2Tag->removeFrame(picFrame, true);
                    }
                }
            }
        }
        return true;
    }

    // FLAC: remove only FrontCover
    if (TagLib::FLAC::File *flacFile = dynamic_cast<TagLib::FLAC::File*>(file.file())) {
        auto pictureList = flacFile->pictureList();
        for (auto *pic : pictureList) {
            if (pic && pic->type() == TagLib::FLAC::Picture::FrontCover) {
                flacFile->removePicture(pic, true);
            }
        }
        return true;
    }

    // MP4
    if (TagLib::MP4::File *mp4File = dynamic_cast<TagLib::MP4::File*>(file.file())) {
        if (mp4File->tag()) {
            mp4File->tag()->removeItem("covr");
        }
        return true;
    }

    // Ogg Vorbis: remove only FrontCover
    if (TagLib::Ogg::Vorbis::File *vorbisFile = dynamic_cast<TagLib::Ogg::Vorbis::File*>(file.file())) {
        if (vorbisFile->tag()) {
            auto pictureList = vorbisFile->tag()->pictureList();
            for (auto *pic : pictureList) {
                if (pic && pic->type() == TagLib::FLAC::Picture::FrontCover) {
                    vorbisFile->tag()->removePicture(pic, true);
                }
            }
        }
        return true;
    }

    // Ogg Opus: remove only FrontCover
    if (TagLib::Ogg::Opus::File *opusFile = dynamic_cast<TagLib::Ogg::Opus::File*>(file.file())) {
        if (opusFile->tag()) {
            auto pictureList = opusFile->tag()->pictureList();
            for (auto *pic : pictureList) {
                if (pic && pic->type() == TagLib::FLAC::Picture::FrontCover) {
                    opusFile->tag()->removePicture(pic, true);
                }
            }
        }
        return true;
    }

    return true;
}

bool Track::saveCoverArt(TagLib::FileRef& file, const QByteArray& imageData)
{
    // Remove existing FrontCover first, leaving any other pictures intact
    removeCoverArt(file);

    TagLib::ByteVector data(imageData.data(), imageData.size());

    // MP3/ID3v2
    if (TagLib::MPEG::File *mpegFile = dynamic_cast<TagLib::MPEG::File*>(file.file())) {
        auto *id3v2Tag = mpegFile->ID3v2Tag(true);
        if (!id3v2Tag) return false;
        auto *frame = new TagLib::ID3v2::AttachedPictureFrame;
        frame->setMimeType("image/png");
        frame->setType(TagLib::ID3v2::AttachedPictureFrame::FrontCover);
        frame->setPicture(data);
        id3v2Tag->addFrame(frame);
        return true;
    }

    // FLAC
    if (TagLib::FLAC::File *flacFile = dynamic_cast<TagLib::FLAC::File*>(file.file())) {
        auto *picture = new TagLib::FLAC::Picture;
        picture->setData(data);
        picture->setMimeType("image/png");
        picture->setType(TagLib::FLAC::Picture::FrontCover);
        flacFile->addPicture(picture);
        return true;
    }

    // MP4
    if (TagLib::MP4::File *mp4File = dynamic_cast<TagLib::MP4::File*>(file.file())) {
        TagLib::MP4::CoverArtList coverList;
        TagLib::MP4::CoverArt cover(TagLib::MP4::CoverArt::PNG, data);
        coverList.append(cover);
        mp4File->tag()->setItem("covr", TagLib::MP4::Item(coverList));
        return true;
    }

    // Ogg Vorbis
    if (TagLib::Ogg::Vorbis::File *vorbisFile = dynamic_cast<TagLib::Ogg::Vorbis::File*>(file.file())) {
        auto *picture = new TagLib::FLAC::Picture;
        picture->setData(data);
        picture->setMimeType("image/png");
        picture->setType(TagLib::FLAC::Picture::FrontCover);
        vorbisFile->tag()->addPicture(picture);
        return true;
    }

    // Ogg Opus
    if (TagLib::Ogg::Opus::File *opusFile = dynamic_cast<TagLib::Ogg::Opus::File*>(file.file())) {
        auto *picture = new TagLib::FLAC::Picture;
        picture->setData(data);
        picture->setMimeType("image/png");
        picture->setType(TagLib::FLAC::Picture::FrontCover);
        opusFile->tag()->addPicture(picture);
        return true;
    }

    // WAV (limited support)
    if (TagLib::RIFF::WAV::File *wavFile = dynamic_cast<TagLib::RIFF::WAV::File*>(file.file())) {
        // WAV files don't typically support embedded images in TagLib
        qWarning() << "Cover art saving not supported for WAV files";
        return false;
    }

    // AIFF (limited support)
    if (TagLib::RIFF::AIFF::File *aiffFile = dynamic_cast<TagLib::RIFF::AIFF::File*>(file.file())) {
        qWarning() << "Cover art saving not supported for AIFF files";
        return false;
    }

    qWarning() << "Cover art saving not supported for this file format";
    return false;
}

}