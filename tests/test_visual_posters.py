"""Verify deterministic source mappings without fetching multimedia."""
import unittest
from visual_posters import selected_movies
class PosterManifest(unittest.TestCase):
    def test_exact_film_id_selection(self):
        manifest={f"{n:04d}":n+1000 for n in range(2,26)}
        chosen=selected_movies(manifest)
        self.assertEqual(len(chosen),26)
        self.assertEqual(chosen[1],"video-0001-14498676883.mp4")
        self.assertEqual(chosen[26],"video-0026-14651386328.mp4")
        self.assertEqual(chosen[9],"video-0009-1009.mp4")
    def test_missing_historical_video_is_error(self):
        with self.assertRaises(ValueError):
            selected_movies({})
if __name__=="__main__":unittest.main()
