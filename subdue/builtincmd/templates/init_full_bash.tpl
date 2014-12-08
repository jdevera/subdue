# This is the full configuration that is required for full support of this
# Subdue sub '${sub_name}' under the Bash shell.
# This text should be evalled by Bash on startup. Add this to your
# ~./bash_profile

# Add this sub to the path
# TODO: Don't do this for thin subs
if ! [[ ":$$PATH:" == *":${sub_bin_dir}:"* ]]; then
    export PATH=${sub_bin_dir}:$$PATH
fi

# Wrapper to handle eval subcommands
function _subdue_${sub_name}_wrapper()
{
    local ret=0
    if [[ -n $$1 ]] && command ${sub_name} --shell bash --is-eval "$$@"; then
        eval "$$(command ${sub_name} --shell bash "$$@")"
        ret=$$?
    else
        command ${sub_name} --shell bash "$$@"
        ret=$$?
    fi
    return $$ret
}

# Use the wrapper by default
alias ${sub_name}=_subdue_${sub_name}_wrapper


