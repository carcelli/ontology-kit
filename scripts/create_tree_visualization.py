import os

from treelib import Tree


def create_directory_tree(root_dir, max_depth=None, exclude_dirs=None, exclude_exts=None):
    """
    Creates a tree visualization of a directory.
    """
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_exts is None:
        exclude_exts = []

    tree = Tree()
    tree.create_node(os.path.basename(root_dir), root_dir)

    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        # Exclude directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

        depth = dirpath.replace(root_dir, '').count(os.sep)
        if max_depth is not None and depth >= max_depth:
            continue

        parent_id = dirpath
        if parent_id == root_dir:
            parent_id = root_dir

        for dirname in dirnames:
            dir_id = os.path.join(dirpath, dirname)
            if not tree.contains(dir_id):
                tree.create_node(dirname, dir_id, parent=parent_id)

        for filename in filenames:
            if not any(filename.endswith(ext) for ext in exclude_exts):
                file_id = os.path.join(dirpath, filename)
                if not tree.contains(file_id):
                    tree.create_node(filename, file_id, parent=parent_id)

    return tree

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a tree visualization of a directory.")
    parser.add_argument("root_dir", type=str, help="The root directory to visualize.")
    parser.add_argument("--max-depth", type=int, help="The maximum depth of the tree.")
    parser.add_argument("--exclude-dirs", type=str, nargs='*', default=['.venv', '.git', '__pycache__', '.pytest_cache', 'htmlcov', 'agent_kit.egg-info'], help="Directories to exclude.")
    parser.add_argument("--exclude-exts", type=str, nargs='*', default=['.pyc', '.pyo', '.pyd'], help="File extensions to exclude.")
    args = parser.parse_args()

    tree = create_directory_tree(args.root_dir, args.max_depth, args.exclude_dirs, args.exclude_exts)
    tree.show()
